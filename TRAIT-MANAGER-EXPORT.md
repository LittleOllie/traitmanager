# Trait Manager export — developer guide

This document describes the JSON files produced by **Trait Manager** in Little Ollie Character Creator, and how to use them to implement hat ↔ glasses compatibility rules in production.

---

## Files to use together

| File | Source | Purpose |
|------|--------|---------|
| `lo-trait-compatibility.json` | Trait Manager → **EXPORT JSON** | Pairwise hat + glasses review results |
| `assets/traits-manifest.json` | Shipped with the app | Full trait catalog (paths, slots, IDs, skin tones, etc.) |

**Do not** use Character Creator’s **EXPORT SELECTION .JSON** (`LO-trait-selection.json`) for compatibility rules. That file only records which traits are ticked “include in randomizer” per slot.

---

## Export file structure

Trait Manager downloads:

**Filename:** `lo-trait-compatibility.json`

```json
{
  "version": 1,
  "exportedAt": "2026-05-27T12:34:56.789Z",
  "completion": {
    "reviewed": 120,
    "total": 5000,
    "percent": 2.4
  },
  "data": {
    "hats_vs_glasses": {
      "bucket-hat-tan": {
        "scream-mask": {
          "status": "allowed",
          "layerMode": "hat_above_glasses",
          "notes": "",
          "reviewedAt": "2026-05-27T12:00:00.000Z"
        }
      }
    }
  }
}
```

### Top-level fields

| Field | Type | Description |
|-------|------|-------------|
| `version` | number | Export format version (currently `1`) |
| `exportedAt` | string (ISO 8601) | When the file was exported |
| `completion.reviewed` | number | Count of hat+glasses pairs with a saved status |
| `completion.total` | number | Total possible pairs (hats × glasses in manifest) |
| `completion.percent` | number | `reviewed / total` as a percentage (one decimal) |
| `data` | object | Compatibility store (see below) |

### `data.hats_vs_glasses`

Nested map:

```
hats_vs_glasses[hatId][glassesId] → entry
```

- **`hatId`** — stable ID for the hat trait (`normalizedName` from manifest).
- **`glassesId`** — stable ID for the glasses/accessories trait (`normalizedName` from manifest).
- **Entry** — review result for that pair.

Example IDs from `assets/traits-manifest.json`:

- Hat: `"bucket-hat-tan"` → `assets/traits/HATS/Bucket Hat - Tan.PNG`
- Glasses: `"scream-mask"` → `assets/traits/GLASSES/Scream Mask.PNG`

Resolve paths and display names via the manifest, not from the compatibility file alone.

---

## Review entry fields

Each `hats_vs_glasses[hatId][glassesId]` object:

| Field | Type | Description |
|-------|------|-------------|
| `status` | string | Outcome of the review (see table below) |
| `layerMode` | string | Which asset draws on top when both are worn |
| `notes` | string | Optional free-text note from the reviewer |
| `reviewedAt` | string (ISO 8601) | When the pair was last saved |

### `status` values

These match the buttons in Trait Manager:

| Status | UI label | Suggested production rule |
|--------|----------|---------------------------|
| `allowed` | ✅ WORKS | Allow the combo. Apply `layerMode` for draw order. |
| `blocked` | ❌ BLOCKED | Disallow this hat + glasses together (filter in randomizer / creator). |
| `swap` | 🔄 SWAP | Allow the combo; layer order should follow `layerMode` (often swapped vs default). |
| `offset` | ⚠ OFFSET | Allow the combo, but flag for possible manual positioning. **No x/y offsets are stored in JSON.** |
| `skipped` | ⏭ SKIPPED | Reviewer skipped for now. Treat as “not decided” unless product says otherwise. |

Statuses are stored lowercase. Import normalises case.

### `layerMode` values

| Value | Meaning |
|-------|---------|
| `hat_above_glasses` | Hat layer has higher z-index than glasses |
| `glasses_above_hat` | Glasses layer has higher z-index than hat |
| `default` | Use app default (creator default is hat above glasses) |

When implementing rendering, read `layerMode` on the pair entry; fall back to your app default if missing or `default`.

---

## Trait IDs (`hatId` / `glassesId`)

IDs in the export are **`normalizedName`** from `assets/traits-manifest.json`:

```json
{
  "slot": "hat",
  "file": "Bucket Hat - Tan.PNG",
  "path": "assets/traits/HATS/Bucket Hat - Tan.PNG",
  "traitName": "Bucket Hat - Tan",
  "normalizedName": "bucket-hat-tan"
}
```

Lookup algorithm:

1. Load manifest `traits[]`.
2. Index by `normalizedName` (and optionally by `path` for debugging).
3. For each `hats_vs_glasses[hatId][glassesId]`, resolve both traits from the manifest.

If an ID in the export is missing from the manifest, log a warning and skip or treat as unknown.

---

## Pairs not in the export

**Only reviewed pairs appear** under `data.hats_vs_glasses`. Untested combinations are omitted, not listed as `"status": "untested"`.

Agree on a default with the product owner, for example:

| Policy | Behaviour |
|--------|-----------|
| **Permissive** | Missing pair → treat as `allowed` with default `layerMode` |
| **Strict** | Missing pair → treat as blocked or hidden until reviewed |
| **Hybrid** | Missing → allowed in creator, blocked in collection randomizer until reviewed |

Document the chosen policy in your app config.

Use `completion.reviewed` and `completion.total` to gauge how complete the dataset is before shipping strict rules.

---

## Snapshot export (optional)

**SAVE SNAPSHOT** downloads `lo-trait-compatibility-snapshot.json`. Same compatibility `data`, plus:

```json
{
  "version": 1,
  "savedAt": "…",
  "completion": { … },
  "state": { … },
  "data": { "hats_vs_glasses": { … } }
}
```

`state` holds Trait Manager UI session (queue index, filter toggles, base skin, etc.). **Production only needs `data`** unless you are restoring a review session.

---

## View Completed Traits (in-app)

Trait Manager includes **VIEW COMPLETED TRAITS** to browse every saved pair:

- **BY GLASSES ORDER** — outer loop glasses, inner loop hats (same sequence as the main review queue).
- **BY HAT ORDER** — outer loop hats, inner loop glasses.
- Preview uses the saved **`layerMode`** for each pair (hat above glasses vs glasses above hat).
- **SWAP LAYER ORDER** toggles stacking and writes the fix back to `data.hats_vs_glasses` immediately (for export).

Shortcuts while the viewer is open: **← / →** prev/next, **S** swap layers, **Esc** close.

---

## Import back into Trait Manager

Trait Manager → **IMPORT JSON** accepts:

- Full export: `{ "data": { "hats_vs_glasses": … } }`
- Or raw store: `{ "hats_vs_glasses": … }`

Imported data is stored in browser `localStorage` under key `lo_trait_compatibility_v2`.

---

## Scope limitations

This export covers **hat ↔ glasses (accessories slot) only**.

It does **not** define rules for:

- Skin ↔ hands / balls
- Hat ↔ hoodies / goo / hair
- Any other trait pairs

Those are handled separately in app code (e.g. `traits-registry.js` skin matching) and are not part of `lo-trait-compatibility.json`.

---

## Example: lookup helper (pseudo-code)

```javascript
function getPairRule(compatJson, manifest, hatNormalizedName, glassesNormalizedName) {
  const entry =
    compatJson?.data?.hats_vs_glasses?.[hatNormalizedName]?.[glassesNormalizedName];

  if (!entry) {
    return { status: 'untested', layerMode: 'hat_above_glasses' }; // or your default policy
  }

  return {
    status: entry.status,
    layerMode: entry.layerMode || 'hat_above_glasses',
    notes: entry.notes || '',
    reviewedAt: entry.reviewedAt,
    hat: manifest.traits.find(t => t.normalizedName === hatNormalizedName),
    glasses: manifest.traits.find(t => t.normalizedName === glassesNormalizedName),
  };
}
```

```javascript
function isComboAllowed(rule, defaultForMissing = 'allow') {
  if (!rule || rule.status === 'untested') {
    return defaultForMissing === 'allow';
  }
  return rule.status !== 'blocked';
}
```

```javascript
function applyLayerOrder(hatEl, glassesEl, layerMode) {
  if (layerMode === 'glasses_above_hat') {
    glassesEl.style.zIndex = 80;
    hatEl.style.zIndex = 70;
  } else {
    hatEl.style.zIndex = 80;
    glassesEl.style.zIndex = 70;
  }
}
```

---

## Recommended handoff checklist

- [ ] `lo-trait-compatibility.json` (latest export after review pass)
- [ ] `assets/traits-manifest.json` (same build / version as the creator)
- [ ] Agreed **default for missing pairs** (permissive vs strict)
- [ ] Agreed handling of `skipped` and `offset`
- [ ] Note that `offset` has no coordinates — layout fixes are manual or a future format version
- [ ] Confirm scope: hat+glasses only; other rules documented separately

---

## Related files in this repo

| Path | Role |
|------|------|
| `index.html` | Trait Manager UI, export/import, `traitId()` / `computeQueue()` |
| `traits-registry.js` | Manifest load, skin/hand matching (not hat/glasses compat file) |
| `assets/traits-manifest.json` | Canonical trait list and `normalizedName` IDs |

---

## Version history

| Version | Notes |
|---------|--------|
| `1` | Initial export: `hats_vs_glasses`, `status`, `layerMode`, `notes`, `reviewedAt` |

If the export format changes, bump `version` in the JSON and update this document.
