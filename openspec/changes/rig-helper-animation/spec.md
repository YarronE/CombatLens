# Behavior

Every animation channel targets an existing reachable scene node and a TRS property. Each clip must drive a skin joint or its ancestor. A clip targeting unrelated mesh/helper nodes alone remains rejected. Matrix/TRS conflicts, duplicate channels, out-of-scene targets and invalid binary values remain rejected. Static preview policy is unchanged.
