# Kansei Radio — radio.kansei-studio.art

Radio sincronizzata, pubblicata come sito statico su Vercel. Non serve nessun server di streaming.
Il player legge `playlist.json` e calcola dall'ora quale brano suona e da che punto,
così tutti gli ascoltatori sentono la stessa cosa nello stesso momento.
La playlist gira in loop a partire dalla data `epoch`.

```
index.html          player (visual audio-reattivi, logo e stile Kansei)
playlist.json       elenco dei brani in onda, con durata
tracks/             MP3 a 128 kbps
tools/genera_playlist.py   rigenera playlist.json dai file in tracks/
vercel.json         cache e header per i file audio
```

## Pubblicazione (una volta sola)

1. Crea un repository (es. `kansei-radio`) con il contenuto di questa cartella e fai il push.
2. Su Vercel: **Add New → Project**, importa il repository.
   Framework preset: **Other**. Nessun comando di build. Output directory: la radice.
3. Nel progetto: **Settings → Domains → Add** `radio.kansei-studio.art`.
   - Se il DNS di kansei-studio.art è già gestito da Vercel, il record viene creato da solo.
   - Altrimenti, nel pannello del dominio aggiungi un record `CNAME radio → cname.vercel-dns.com`
     (Vercel mostra il valore esatto da usare).
4. Il certificato HTTPS viene emesso in automatico in pochi minuti.

In alternativa al repository: `npm i -g vercel`, poi da questa cartella `vercel --prod`.

## Aggiungere o cambiare brani

1. Copia i nuovi MP3 in `tracks/` (128 kbps, con dissolvenza in entrata e in uscita).
   L'ordine di riproduzione è quello alfabetico dei nomi: `13-titolo.mp3`, `14-...`
2. Lancia `python3 tools/genera_playlist.py` (richiede ffmpeg/ffprobe).
3. Fai il commit e il push: Vercel ripubblica da solo.

Cambiando i brani cambia la durata totale del loop, quindi chi ascolta in quel momento
potrebbe saltare a un altro punto al successivo riallineamento. È normale.

Per far ripartire il palinsesto dal primo brano a un'ora precisa, cambia `epoch` in
`playlist.json` (formato ISO, es. `"2026-12-01T00:00:00Z"`).

## Note

- **Fallback**: se `playlist.json` non è raggiungibile, il player usa il motore
  generativo nel browser e lo segnala con "Demo generativa".
- **Futuro stream live (AzuraCast)**: in `index.html` imposta `STREAM_URL` (e, se serve,
  `NOWPLAYING_URL`). Lo stream ha la precedenza; se non risponde, il player torna alla
  playlist sincronizzata. Verifica con `curl -I <stream>` che ci sia
  `access-control-allow-origin`, altrimenti imposta `STREAM_CORS = false`.
- **Banda**: a 128 kbps un ascoltatore consuma circa 58 MB all'ora. I file sono serviti
  con cache di un anno: per sostituire un brano usa un nome di file nuovo.
- **Piano Vercel**: per un uso commerciale serve il piano Pro (il piano Hobby è solo personale).
