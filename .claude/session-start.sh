#!/bin/bash

echo "==================================="
echo "🔄 Sincronizzazione Repository"
echo "==================================="
echo ""

# Ottieni il branch corrente
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "❌ Errore: Non siamo in un repository git"
    exit 1
fi

echo "📍 Branch corrente: $CURRENT_BRANCH"
echo ""

# Fetch dal remoto
echo "📥 Scarico informazioni dal repository remoto..."
if git fetch origin "$CURRENT_BRANCH" 2>&1; then
    echo "✅ Fetch completato"
else
    echo "⚠️  Attenzione: Errore durante il fetch (potrebbe essere un problema di rete)"
fi
echo ""

# Controlla lo stato
echo "📊 Stato del repository:"
git status --short --branch
echo ""

# Controlla se ci sono commit remoti da scaricare
LOCAL=$(git rev-parse @ 2>/dev/null)
REMOTE=$(git rev-parse @{u} 2>/dev/null)

if [ $? -ne 0 ]; then
    echo "⚠️  Il branch non traccia un branch remoto"
    echo ""
    exit 0
fi

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "✅ Il tuo repository locale è già aggiornato!"
elif git merge-base --is-ancestor "$LOCAL" "$REMOTE" 2>/dev/null; then
    echo "📥 Ci sono nuovi commit sul remoto. Sincronizzazione in corso..."
    if git pull origin "$CURRENT_BRANCH" 2>&1; then
        echo "✅ Repository sincronizzato con successo!"
    else
        echo "❌ Errore durante il pull. Controlla i conflitti."
        exit 1
    fi
else
    echo "⚠️  Attenzione: Il tuo branch locale ha commit che non sono sul remoto"
    echo "   Usa 'git push' per caricarli o 'git pull' con cautela se ci sono conflitti"
fi

echo ""
echo "==================================="
echo "✅ Sincronizzazione completata"
echo "==================================="
