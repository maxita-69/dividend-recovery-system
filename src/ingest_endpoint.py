# =========================================================================
# /ingest — endpoint unico che riceve il blocco handoff e scrive nel DB
# in una sola transazione atomica.
#
# Da integrare in /opt/trading_brain/main.py:
#   1. I MODELLI Pydantic qui sotto vanno AGGIUNTI a quelli già esistenti
#      (non sostituiscono Decision / SessionStart / SessionEnd, che restano
#      vivi per retrocompatibilità).
#   2. L'IMPORT `import json` va in cima al file se non c'è già
#      (oggi è dentro a /session/end — meglio in cima, è usato anche qui).
#   3. La FUNZIONE `ingest_handoff` va aggiunta in fondo a main.py.
# =========================================================================

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Literal


# ---- Modelli del blocco handoff -----------------------------------------

class HandoffSession(BaseModel):
    llm_used: Literal["claude", "kimi", "minimax"]
    goal: str = Field(..., min_length=1)
    outcome: Literal["success", "partial", "blocked"]
    summary: str = Field(..., min_length=1)


class HandoffDecision(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    decision_taken: str = Field(..., min_length=1)
    rationale: str = Field(..., min_length=1)


class HandoffFile(BaseModel):
    path: str = Field(..., min_length=1, max_length=500)
    action: Literal["created", "modified", "deleted"]
    description: str = Field(..., min_length=1)


class Handoff(BaseModel):
    """Contratto v1 del blocco handoff. Campi rigidi: session + next_task."""
    session: HandoffSession
    next_task: str = Field(..., min_length=1)
    decisions: List[HandoffDecision] = Field(default_factory=list)
    files_touched: List[HandoffFile] = Field(default_factory=list)
    open_problems: List[str] = Field(default_factory=list)

    @field_validator("open_problems")
    @classmethod
    def strip_empty_problems(cls, v: List[str]) -> List[str]:
        # Tollera spazi/stringhe vuote prodotte dagli LLM
        return [p.strip() for p in v if p and p.strip()]


# ---- Endpoint -----------------------------------------------------------

@app.post("/ingest")
async def ingest_handoff(data: Handoff):
    """
    Ingerisce un blocco handoff completo in una sola transazione.
    Scrive sessione, decisioni, files (UPSERT), e aggiorna project_state.

    Ritorna un riepilogo di cosa è stato scritto: utile per il CLI `ingest`
    e per accorgersi se l'LLM si è inventato campi strani.
    """
    db = await get_db()
    try:
        async with db.transaction():
            # 1. Crea la sessione: started_at = now() di default,
            #    ended_at lo settiamo qui perché è una sessione "chiusa".
            session_row = await db.fetchrow(
                """
                INSERT INTO sessions (llm_used, goal, summary, outcome, ended_at)
                VALUES ($1, $2, $3, $4, now())
                RETURNING id, started_at, ended_at
                """,
                data.session.llm_used,
                data.session.goal,
                data.session.summary,
                data.session.outcome,
            )
            session_id = session_row["id"]

            # 2. Inserisce le decisioni (una riga per decisione, attaccate
            #    alla sessione appena creata).
            decision_ids = []
            for d in data.decisions:
                row = await db.fetchrow(
                    """
                    INSERT INTO decisions (topic, decision_taken, rationale, session_id)
                    VALUES ($1, $2, $3, $4)
                    RETURNING id
                    """,
                    d.topic, d.decision_taken, d.rationale, session_id,
                )
                decision_ids.append(row["id"])

            # 3. UPSERT dei files in code_index. Una riga per file_path:
            #    se esiste, aggiorniamo description/status/session/updated_at.
            files_written = []
            for f in data.files_touched:
                row = await db.fetchrow(
                    """
                    INSERT INTO code_index (file_path, description, status, session_id, updated_at)
                    VALUES ($1, $2, $3, $4, now())
                    ON CONFLICT (file_path) DO UPDATE SET
                        description = EXCLUDED.description,
                        status      = EXCLUDED.status,
                        session_id  = EXCLUDED.session_id,
                        updated_at  = now()
                    RETURNING id, (xmax = 0) AS inserted
                    """,
                    f.path, f.description, f.action, session_id,
                )
                # xmax=0 → INSERT vero, altrimenti UPDATE. Utile per il summary.
                files_written.append({
                    "path": f.path,
                    "action": "inserted" if row["inserted"] else "updated",
                })

            # 4. Aggiorna project_state. Strategia:
            #    - last_task_completed ← session.goal (il task appena finito)
            #    - next_task ← handoff.next_task (rigido, sempre presente)
            #    - open_problems ← merge dedup (vecchi + nuovi)
            #    - current_phase NON tocchiamo (è una decisione manuale tua,
            #      cambia raramente; se serve la cambi in psql)

            existing_state = await db.fetchrow(
                "SELECT id, open_problems FROM project_state ORDER BY updated_at DESC LIMIT 1"
            )

            old_problems: List[str] = []
            if existing_state and existing_state["open_problems"]:
                raw = existing_state["open_problems"]
                # asyncpg restituisce JSONB come stringa → la parsiamo
                if isinstance(raw, str):
                    try:
                        raw = json.loads(raw)
                    except json.JSONDecodeError:
                        raw = []
                if isinstance(raw, list):
                    old_problems = [str(x).strip() for x in raw if str(x).strip()]

            # Dedup preservando l'ordine: prima i vecchi, poi i nuovi non duplicati
            merged_problems: List[str] = []
            seen = set()
            for p in old_problems + data.open_problems:
                key = p.lower()
                if key not in seen:
                    seen.add(key)
                    merged_problems.append(p)

            if existing_state:
                await db.execute(
                    """
                    UPDATE project_state
                    SET last_task_completed = $1,
                        next_task           = $2,
                        open_problems       = $3::jsonb,
                        updated_at          = now()
                    WHERE id = $4
                    """,
                    data.session.goal,
                    data.next_task,
                    json.dumps(merged_problems),
                    existing_state["id"],
                )
            else:
                # Prima riga in project_state (caso edge: DB appena inizializzato)
                await db.execute(
                    """
                    INSERT INTO project_state
                        (current_phase, last_task_completed, next_task, open_problems)
                    VALUES ('setup_infrastructure', $1, $2, $3::jsonb)
                    """,
                    data.session.goal,
                    data.next_task,
                    json.dumps(merged_problems),
                )

        # Tutto committato. Riepilogo per il chiamante (CLI `ingest`).
        return {
            "status": "ok",
            "session_id": session_id,
            "decisions_inserted": len(decision_ids),
            "files_written": files_written,
            "project_state_updated": {
                "last_task_completed": data.session.goal,
                "next_task": data.next_task,
                "open_problems_count": len(merged_problems),
                "open_problems_added": len(merged_problems) - len(old_problems),
            },
        }
    finally:
        await db.close()