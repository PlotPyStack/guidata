# -----------------------------------------------------------------------------
#  Copyright (C) 2019 Alberto Sottile
#
#  Distributed under the terms of the 3-clause BSD License.
# -----------------------------------------------------------------------------

# Upstream imports darkdetect absolutely; use a relative import for this vendored copy.
from . import theme

print("Current theme: {}".format(theme()))