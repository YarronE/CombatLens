# Spec

Existing seconds mappings remain backward compatible. A frames mapping requires finite positive seconds_per_unit and registered source dependencies, consistent endpoints and a matching sequence unit and duration. Raw event values remain immutable. Mapping conversion scales coordinates only; playback speed remains play_rate. Frame seek uses registered samples, with float32 endpoint tolerance. Mixed or unproven event coordinates remain unseekable. Existing range, loop, frame step and draft editing work in the selected proven coordinate unit.
