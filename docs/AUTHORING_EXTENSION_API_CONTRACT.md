# Authoring Extension API Contract v2

Authoring extensions let plugins/modules declare local editor panels, form
schemas, validation refs, and preview refs. They are declarative metadata only.

## Rules

- Extensions do not execute arbitrary code.
- Save requires AuthoringValidationGate.
- Extensions cannot directly modify active GameState.
- Extensions cannot read `.env` or API keys.
- Hidden fields must not be displayed in player UI.

