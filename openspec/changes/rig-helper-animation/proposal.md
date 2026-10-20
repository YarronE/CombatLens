# Accept source-backed rig helper transforms

A native skeletal export contains joint channels plus root and attachment transforms. The server currently rejects every channel whose target is not in the skin joint array, even when the clip also animates real joints. Permit visible scene transforms while retaining a required rig-driving channel and all byte, hierarchy, accessor, geometry and source checks.
