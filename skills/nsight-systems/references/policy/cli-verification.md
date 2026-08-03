# CLI Verification Policy

Live `nsys` help is authoritative for the user's installed binary.

Before stating exact syntax, flags, defaults, or valid values, inspect live help. Packaged docs can explain concepts but may describe a different release. If live help and packaged docs differ, say which source was used and prefer live help for the installed CLI.

Never invent shorthand flags, recipe flags, environment variables, or command forms. Use placeholders such as `<report.nsys-rep>` and `<output-name>` instead of concrete-looking fake paths.
