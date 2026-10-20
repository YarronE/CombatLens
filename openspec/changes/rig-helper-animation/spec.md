# Behavior

Every animation channel targets an existing reachable scene node and a TRS property. Each clip must drive a skin joint or its ancestor. A clip targeting unrelated mesh/helper nodes alone remains rejected. Matrix/TRS conflicts, duplicate channels, out-of-scene targets and invalid binary values remain rejected. Static preview policy is unchanged.

Native models can bind separate meshes in different spaces. Preserve each actual skin, joint list and inverse-bind matrix set. Validate a shared mesh against every skin that binds it. Do not force different source matrices into one invented global skin. The browser accepts multiple independently checked skins.
