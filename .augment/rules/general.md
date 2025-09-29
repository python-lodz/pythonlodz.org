---
type: "always_apply"
description: "Example description"
---

use Pathlib
do not uses classes to group tests, use functions in files and folders only
always use newes possible typing syntax (avoid typing module)
use ruff for linting instead of pylint
use ruff for formatting instead of black
use logging.getLogger(**name**) instead of print statements
use expressive function names over comments, instead of writing comments generate function with proper name
use absolute imports
avoid overengineering and keep simple, related concepts together
avoid unnecessary exception handling, prefer stric types, input verification and simpler code later
when supported by the lib use Annotation syntax
use git add with files list, never add all files to the repository
