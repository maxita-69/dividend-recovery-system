#!/usr/bin/env bash
# =============================================================================
# genera_stato.sh — Fotografia AUTOMATICA dello stato del progetto.
#
# Filosofia: lo stato non si scrive a mano, si DERIVA dalla realta'.
# Git, systemctl, docker e l'albero dei file sono gia' la verita'.
# Questo script li legge ogni volta -> STATO.md non puo' andare stantio.
#
# Uso:
#   ./genera_stato.sh        aggiorna STATO.md e lo stampa
#   stato                    (se metti l'alias nel .bashrc, vedi sotto)
#
# Suggerimento .bashrc:
#   alias stato='~/dividend-recovery-system/genera_stato.sh'
# =============================================================================

set -uo pipefail

REPO="${REPO:-$HOME/dividend-recovery-system}"
INTENTO="$REPO/INTENTO.md"
OUT="$REPO/STATO.md"

# Servizi systemd da controllare (modifica la lista se serve)
SERVIZI=(trading-brain code-server nginx tailscaled fail2ban)

cd "$REPO" 2>/dev/null || { echo "ERRORE: repo non trovato in $REPO"; exit 1; }

{
  echo "# 📍 STATO PROGETTO — $(date '+%Y-%m-%d %H:%M')"
  echo
  echo "> Generato automaticamente da \`genera_stato.sh\`."
  echo "> Le sezioni sotto sono LETTE DAL SISTEMA REALE: non modificarle a mano."
  echo "> Per cambiare obiettivo / prossimo passo, modifica \`INTENTO.md\` e rilancia lo script."
  echo

  # ---------------------------------------------------------------------------
  # 1. INTENTO — l'UNICA parte scritta da te (5 righe)
  # ---------------------------------------------------------------------------
  echo "## 🎯 Intento corrente (da INTENTO.md)"
  echo
  if [[ -f "$INTENTO" ]]; then
    cat "$INTENTO"
  else
    echo "> ⚠️ INTENTO.md non esiste ancora. Crealo con queste 5 righe:"
    echo '> ```'
    echo "> **Fase:** ..."
    echo "> **Ultima cosa fatta:** ..."
    echo "> **Prossimo passo:** ..."
    echo "> **Domande aperte:** ..."
    echo "> **Assistente ultima sessione:** ..."
    echo '> ```'
  fi
  echo

  # ---------------------------------------------------------------------------
  # 2. GIT — la verita' sul codice
  # ---------------------------------------------------------------------------
  echo "## 🌿 Git"
  echo '```'
  echo "Branch attivo: $(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '(no git)')"
  echo
  echo "Ultimi commit:"
  git log --oneline -8 2>/dev/null || echo "(git non disponibile)"
  echo
  echo "Modifiche NON committate:"
  if git diff --quiet 2>/dev/null && git diff --cached --quiet 2>/dev/null; then
    echo "(nessuna — working tree pulito)"
  else
    git status --short 2>/dev/null
  fi
  echo '```'
  echo

  # ---------------------------------------------------------------------------
  # 3. SERVIZI systemd
  # ---------------------------------------------------------------------------
  echo "## ⚙️ Servizi systemd"
  echo '```'
  for s in "${SERVIZI[@]}"; do
    st=$(systemctl is-active "$s" 2>/dev/null || echo "sconosciuto")
    printf "%-16s %s\n" "$s" "$st"
  done
  echo '```'
  echo

  # ---------------------------------------------------------------------------
  # 4. DOCKER
  # ---------------------------------------------------------------------------
  echo "## 🐳 Docker (container attivi)"
  echo '```'
  docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' 2>/dev/null \
    || echo "(docker non disponibile o nessun container)"
  echo '```'
  echo

  # ---------------------------------------------------------------------------
  # 5. STRUTTURA DEL CODICE
  # ---------------------------------------------------------------------------
  echo "## 📂 Struttura cartelle (max 2 livelli)"
  echo '```'
  find . -maxdepth 2 -type d \
    -not -path '*/node_modules*' -not -path '*/venv*' \
    -not -path '*/.git*' -not -path '*/__pycache__*' -not -path '*/dist*' \
    2>/dev/null | sort
  echo '```'
  echo

  echo "## 🐍 File Python piu' grossi"
  echo '```'
  find . -name "*.py" -not -path '*/venv*' -not -path '*/node_modules*' 2>/dev/null \
    | xargs wc -l 2>/dev/null | sort -n | tail -15
  echo '```'

} > "$OUT"

# Stampa a video + conferma
cat "$OUT"
echo
echo ">>> Stato aggiornato e scritto in: $OUT"
