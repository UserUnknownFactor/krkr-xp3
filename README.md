KiriKiri XP3-archive unpack/repack tool
======

Unpacks an .xp3 archive to a directory or packs a directory, including all subdirectories, into an .xp3 archive.

Use `-f` flag to flatten the directory structure for patches and `-c` flag to provide a known cypher.

Examples
------
- Unpack:
    ```
    xp3 -s -u "C:\game directory\data.xp3" "C:\game directory\data"
    xp3 -u -c nekov0 patch.xp3 patch
    ```
- Repack:
    ```
    xp3 -f -r -c nekov0 patch patch.xp3
    ```

Original script by [Edward Keyes](http://www.insani.org/tools/) and [SmilingWolf](https://bitbucket.org/SmilingWolf/xp3tools-updated), Python 3 rewrite by Awakening.
