<img width="1338" height="1044" alt="image" src="https://github.com/user-attachments/assets/1a2306da-6e12-4694-8b98-138d987134df" />



UEFN Auto Type Organizer

A Python-based asset organization tool for Unreal Editor for Fortnite
(UEFN) that automatically sorts project assets into a structured folder
hierarchy based on asset type and naming context.

------------------------------------------------------------------------

Overview

This tool scans a specified Content Browser folder and reorganizes
assets into a consistent structure such as:

/YourProject/_Organized/Meshes/Trees

/YourProject/_Organized/Textures/Surface

It is designed to reduce manual asset management, improve project
organization, and maintain valid references using Unreal’s built-in
redirector system.

------------------------------------------------------------------------

Features

-   Scans any Content Browser folder
-   Detects asset types automatically (Textures, Meshes, Materials,
    Sounds, etc.)
-   Organizes assets into structured folders by type and category
-   Groups assets logically based on naming (e.g., Trees, Rocks, UI,
    VFX)
-   Option to include all assets or only those used by the current level
-   Skips assets that are already organized
-   Skips assets that already exist at the destination
-   Automatically creates destination folders if they do not exist
-   Uses Unreal’s native move system to preserve references
-   Automatically saves assets after moving to prevent data loss

------------------------------------------------------------------------

Installation

1.  Download the Python script
2.  Open your project in UEFN
3.  Enable Python scripting: Project → Project Settings → Enable Python Scripting
4.  Open the Python console at the bottom of the editor
5.  Change the mode from: Python (REPL) → Python
6.  Run the script using one of the following methods

Method A (Recommended) - Open the .py file in a text editor - Copy all
contents - Paste into the Python console in UEFN - Press Enter

Method B - Execute the script directly using Python execution tools

The tool window will open after execution.

------------------------------------------------------------------------

Usage

1.  Set Scan Root (Required)

You must set the scan root to your project’s main content folder.

Example: MyProject

Set the scan root to: /MyProject

Do not include quotes.

------------------------------------------------------------------------

2.  Set Organized Root Name

This defines the destination folder where assets will be moved.

Example: _Organized (The underscore is mandatory)

Result: /MyProject/_Organized/

-   If the folder does not exist, it will be created automatically

------------------------------------------------------------------------

3.  Select Asset Types

-   Textures
-   Meshes
-   Materials
-   Sounds
-   Blueprints
-   etc.

------------------------------------------------------------------------

4.  Scan Options

Include assets not used by the current level

-   Enabled → organizes all assets in the scan root

-   Disabled → only organizes assets referenced by the currently loaded
    level

-   This is useful for focusing only on actively used content

------------------------------------------------------------------------

5.  Scan

-   Analyze assets in the selected folder
-   Categorize them
-   Preview the resulting structure

------------------------------------------------------------------------

6.  Organize

-   Create folder structure
-   Move assets
-   Maintain references via redirectors
-   Skip duplicates and already organized assets

------------------------------------------------------------------------

Important Notes

Performance

-   Large projects may take time to process
-   Moving many assets will increase execution time

Stability

-   Do not move the tool window while assets are being moved
-   Doing so may cause UEFN to crash

Auto-Save Behavior

-   Assets are automatically saved after being moved
-   This reduces risk of data loss or corruption

------------------------------------------------------------------------

Post-Process (Required)

After the tool finishes:

1.  Right-click your project root folder in the Content Browser
2.  Select: Update Redirector References

-   This step is required to clean up redirectors created during asset
    movement

------------------------------------------------------------------------

How It Works

-   Uses Unreal’s Asset Registry to scan assets
-   Uses EditorAssetLibrary.rename_asset() to move assets safely
-   Builds folder structure dynamically based on:
    -   Asset type
    -   Asset naming patterns
-   Preserves references through Unreal’s redirector system

------------------------------------------------------------------------

Example

Before: /MyProject/RandomFolder/blahblahblah/heeheehaahaa/SM_Tree_01 

/MyProject/RandomStuff/blahblahblah/heeheehaahaa/T_Grass

After: /MyProject/_Organized/Meshes/Trees/SM_Tree_01

/MyProject/_Organized/Textures/Foliage/T_Grass

------------------------------------------------------------------------

Recommendations

-   Use level-only filtering when organizing production-ready assets
-   Use full scan mode when cleaning up entire projects
-   The tool can be safely run multiple times without duplicating work

------------------------------------------------------------------------

Summary

This tool provides a fast, reliable way to:

-   Organize large asset libraries
-   Enforce consistent structure
-   Reduce manual workload
-   Maintain clean and production-ready projects
