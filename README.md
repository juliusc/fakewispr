## Installation

```
conda env create -f environment.yml
conda activate fakewispr
```

## Running server

```
API_KEY=<openrouter API key> python server.py
```

## Usage

Navigate to `localhost:8080`

Hold down space bar to talk. AI processing of speech and text only happens when you release the space bar.

## Key features

- Incremental (but not real-time) processing of transcripts.
- Entire-transcript editing, issuing of commands like "delete the last sentence", "change X to Y".

## Bugs
- Microphone startup time on the client causes the first ~0.5 seconds between hitting space bar to be dropped. Waiting a moment before speaking helps.
- Sending multiple sentences before they are finished processing does work but it may be confusing in the UI.

## Demo interaction

Try reading this line by line, holding space bar for each line and releasing between each, and waiting for clean transcript to finish to observe the results.

- "I'm going to tell you a story about two brothers."
- "The brothers were named Johnny and Bill, actually no, Bob and Hank.
- "Bob and Hank went apple-picking with their parents.
- "Change that last sentence, they went cherry-picking."
- "Okay actually they were two sisters named Alice and Jill. Change the whole story to reflect that."