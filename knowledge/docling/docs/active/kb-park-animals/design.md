# Knowledge Base: Park Animals Expansion

**Goal:** Build KB entries for 25 missing park animal species using multiple authoritative sources, with group + species-specific entries.

---

## Current State

- **SQLite KB**: 71 animals
- **Park animals covered**: 17/42 (40%)
- **Gap**: 25 species need KB entries

## Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Granularity** | Group + species combo | "Monkey" overview + "Cotton-top Tamarin" specific |
| **Sources** | San Diego Zoo + NatGeo Kids + A-Z Animals | Multiple sources for broader coverage |
| **Non-park animals** | Deprioritize via category metadata | Keep but mark as `general` vs `park_animal` |

---

## Species to Add (25 + species-specific variants)

### Priority 1: Interactive/Popular (kids ask about these)
| Group | Specific Species | Sources to Try |
|-------|------------------|----------------|
| monkey | Cotton-top Tamarin, Common Marmoset | San Diego Zoo, A-Z Animals |
| porcupine | African Crested Porcupine | San Diego Zoo, NatGeo Kids |
| serval | African Serval | San Diego Zoo, A-Z Animals |
| gibbon | Lar/White-handed Gibbon | San Diego Zoo |
| chinchilla | Long-tailed Chinchilla | A-Z Animals, NatGeo Kids |

### Priority 2: Unique/Interesting
| Group | Specific Species | Sources to Try |
|-------|------------------|----------------|
| kookaburra | Laughing Kookaburra | A-Z Animals, Wikipedia |
| cavy | Patagonian Mara | A-Z Animals |
| coati | Mountain Coati | San Diego Zoo, A-Z Animals |
| nilgai | Blue Bull Antelope | A-Z Animals, Wikipedia |
| zebu | Indian Humped Cattle | A-Z Animals, Wikipedia |

### Priority 3: Reptiles/Birds/Misc
| Group | Specific Species | Sources to Try |
|-------|------------------|----------------|
| crane | East African Crowned Crane | San Diego Zoo |
| peacock | Indian Peafowl | San Diego Zoo, A-Z Animals |
| turkey | Wild Turkey | NatGeo Kids, A-Z Animals |
| raven | Common Raven | A-Z Animals |
| deer | Fallow Deer | A-Z Animals |
| hedgehog | Four-toed Hedgehog | A-Z Animals |
| snake | Ball Python, Indigo Snake | San Diego Zoo, A-Z Animals |
| frog | White's Tree Frog | A-Z Animals |
| gecko | Leaf-tailed Gecko | A-Z Animals |
| skink | Blue-tongued Skink | San Diego Zoo, A-Z Animals |
| tegu | Argentine Tegu | A-Z Animals |
| scorpion | Emperor Scorpion | A-Z Animals |
| squirrel monkey | Common Squirrel Monkey | San Diego Zoo |
| dog | Anatolian Shepherd | AKC, A-Z Animals |

---

## Implementation Plan

### Phase 1: Build Content Fetcher Script
**File:** `scripts/build_kb_park_animals.py`

1. Define species list with group name + specific types + source URLs
2. Fetch content from each source (WebFetch or requests)
3. Extract kid-friendly facts (diet, habitat, fun facts, behaviors)
4. Format for SQLite insertion

### Phase 2: Populate SQLite KB
1. Insert animals into `kb_animals` with category='park_animal'
2. Insert source content into `kb_sources`
3. Handle duplicates gracefully (upsert)

### Phase 3: Add Park Prioritization
1. Update `kb_animals` category for existing park animals
2. Modify RAG search to boost park animals (optional)

### Phase 4: Rebuild Index
1. Trigger `IndexerService.rebuild_index()`
2. Verify chunk counts

### Phase 5: Testing
1. Query each new species
2. Verify species-specific facts appear
3. Test park context integration

---

## Source URLs Template

```python
SOURCES = {
    "san_diego_zoo": "https://animals.sandiegozoo.org/animals/{slug}",
    "a_z_animals": "https://a-z-animals.com/animals/{slug}/",
    "natgeo_kids": "https://kids.nationalgeographic.com/animals/{category}/{slug}",
}
```

---

## Success Criteria

- [ ] 25+ new species added to SQLite KB
- [ ] Species-specific entries where applicable
- [ ] All entries have at least 1 source with content
- [ ] LanceDB rebuilt with new chunks
- [ ] Test queries return relevant park animal facts
