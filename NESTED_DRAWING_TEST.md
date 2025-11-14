# Nested Drawing Test Steps

## Setup
1. Start the app: `python3 app.py`
2. Load your dataset (with the person box image)
3. Switch to **Edit Mode** (button or default)
4. Load/create the image with the person box (the one you already drew)

## Test Procedure
1. **Verify Drawing Mode is OFF** by default
   - Status bar should say "Edit Mode Enabled"
   - Click inside the person box → it should **select the box** (labels panel updates)

2. **Turn ON Drawing Mode** by pressing **M**
   - Status bar should say "Drawing mode enabled"
   - The person box should still be visible

3. **Click inside the person box**
   - You should see logs: `[NESTED_DRAW] ✓ STARTING NESTED DRAW`
   - The start_pos should be set to your click position
   - `parent_box_bounds` should show the person box coordinates

4. **Drag mouse inside the person box**
   - You should see logs: `[NESTED_DRAW] mouseMoveEvent`
   - A **GREEN preview box** should appear and follow your mouse (constrained to person box)
   - Size of preview box should update as you drag

5. **Release mouse to finalize**
   - A class selection dialog should appear
   - Choose a class (e.g., "safety_vest" or "helmet")
   - New box should be added inside the person box

## Expected Logs (IMPORTANT)
Watch terminal output for these lines:
- `[NESTED_DRAW] Found X boxes under cursor` — shows detection working
- `[NESTED_DRAW] ✓ STARTING NESTED DRAW` — nested drawing started successfully
- `[NESTED_DRAW] mouseMoveEvent: parent_box_bounds=...` — move events being tracked
- `[NESTED_DRAW] current_box set to (...)` — preview box coordinates

## Troubleshooting
If you see:
- `[NESTED_DRAW] Not in drawing mode` → You didn't press M or M didn't work
- `[NESTED_DRAW] Found 0 boxes under cursor` → Your click is outside the person box
- No green preview → Check if current_box is being set (check logs)

## Reset
If something breaks:
1. Press **X** to disable drawing mode
2. Press **M** again to re-enable it
3. Try again
