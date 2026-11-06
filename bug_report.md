#Lab 06 Bug Report: 

| Bug | Test(s) that failed |
| --- | --- |
| 1 - POST returns incorrect status | `test_create_artwork` (FAILED), `test_create_artwork_is_saved` (ERROR), `test_update_artwork` (ERROR), `test_delete_artwork` (ERROR), `test_create_duplicate` (ERROR), `test_create_duplicate_ignores_case` (ERROR), `test_update_same_title_and_artist_is_allowed` (ERROR) |
| 2 - Case-sensitive duplicate checking | `test_create_duplicate_ignores_case` |
| 3 - Artwork counts as a duplicate of itself | `test_update_same_title_and_artist_is_allowed` |
| 4 - DELETE does not delete artwork | `test_delete_artwork` |
| 5 - Artist filtering only matches the beginning of a name | `test_filter_by_artist[lowercase-partial]` |

All five intentionally introduced bugs were detected
by the automated test suite.

After each bug was identified, the original code
was restored.

The final test suite successfully passed all 33 tests.