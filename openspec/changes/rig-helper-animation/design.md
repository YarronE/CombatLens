# Design

After scene reachability and parent validation, derive the set of skin joints and all their ancestors. Validate every channel against the active scene, count channels in the derived rig set and reject a clip without any. Browser binding checks should use the same ancestor relationship. This handles real native skeleton root/helper tracks without inventing joints or altering source inverse binds. Keep the existing editor layout.

Native models can bind separate meshes in different spaces. Preserve each actual skin, joint list and inverse-bind matrix set. Validate a shared mesh against every skin that binds it. Do not force different source matrices into one invented global skin. The browser accepts multiple independently checked skins.
