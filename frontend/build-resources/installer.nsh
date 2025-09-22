# Custom NSIS installer script for Photo Search & Navigation
# This script provides additional installer customization

!include "MUI2.nsh"
!include "FileFunc.nsh"

# Installer info
Name "Photo Search & Navigation"
OutFile "PhotoSearchSetup.exe"
InstallDir "$PROGRAMFILES\PhotoSearch"
RequestExecutionLevel admin

# Variables
Var StartMenuFolder

# Modern UI Configuration
!define MUI_ABORTWARNING
!define MUI_ICON "icon.ico"
!define MUI_UNICON "icon.ico"

# Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "license.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY

# Start Menu Folder Page Configuration
!define MUI_STARTMENUPAGE_REGISTRY_ROOT "HKCU"
!define MUI_STARTMENUPAGE_REGISTRY_KEY "Software\PhotoSearch"
!define MUI_STARTMENUPAGE_REGISTRY_VALUENAME "Start Menu Folder"
!insertmacro MUI_PAGE_STARTMENU Application $StartMenuFolder

!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

# Languages
!insertmacro MUI_LANGUAGE "English"

# Installer Sections
Section "Core Application" SecCore
    SectionIn RO  # Required section

    SetOutPath "$INSTDIR"

    # Install application files
    File /r "dist\*.*"

    # Create uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"

    # Registry entries
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PhotoSearch" "DisplayName" "Photo Search & Navigation"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PhotoSearch" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PhotoSearch" "Publisher" "Photo Search Team"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PhotoSearch" "DisplayVersion" "1.0.0"

    # File associations
    WriteRegStr HKCR ".jpg\DefaultIcon" "" "$INSTDIR\PhotoSearch.exe,0"
    WriteRegStr HKCR ".jpeg\DefaultIcon" "" "$INSTDIR\PhotoSearch.exe,0"
    WriteRegStr HKCR ".png\DefaultIcon" "" "$INSTDIR\PhotoSearch.exe,0"

SectionEnd

Section "Desktop Shortcut" SecDesktop
    CreateShortCut "$DESKTOP\Photo Search.lnk" "$INSTDIR\PhotoSearch.exe"
SectionEnd

Section "Start Menu Shortcuts" SecStartMenu
    !insertmacro MUI_STARTMENU_WRITE_BEGIN Application
        CreateDirectory "$SMPROGRAMS\$StartMenuFolder"
        CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Photo Search.lnk" "$INSTDIR\PhotoSearch.exe"
        CreateShortCut "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
    !insertmacro MUI_STARTMENU_WRITE_END
SectionEnd

# Section descriptions
LangString DESC_SecCore ${LANG_ENGLISH} "Core application files (required)"
LangString DESC_SecDesktop ${LANG_ENGLISH} "Create desktop shortcut"
LangString DESC_SecStartMenu ${LANG_ENGLISH} "Create Start Menu shortcuts"

!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
    !insertmacro MUI_DESCRIPTION_TEXT ${SecCore} $(DESC_SecCore)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecDesktop} $(DESC_SecDesktop)
    !insertmacro MUI_DESCRIPTION_TEXT ${SecStartMenu} $(DESC_SecStartMenu)
!insertmacro MUI_FUNCTION_DESCRIPTION_END

# Uninstaller
Section "Uninstall"
    # Remove files
    RMDir /r "$INSTDIR"

    # Remove shortcuts
    Delete "$DESKTOP\Photo Search.lnk"

    !insertmacro MUI_STARTMENU_GETFOLDER Application $StartMenuFolder
    Delete "$SMPROGRAMS\$StartMenuFolder\Photo Search.lnk"
    Delete "$SMPROGRAMS\$StartMenuFolder\Uninstall.lnk"
    RMDir "$SMPROGRAMS\$StartMenuFolder"

    # Remove registry entries
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PhotoSearch"
    DeleteRegKey /ifempty HKCU "Software\PhotoSearch"

SectionEnd

# Functions
Function .onInit
    # Check for existing installation
    ReadRegStr $0 HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PhotoSearch" "UninstallString"
    StrCmp $0 "" done

    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION \
        "Photo Search is already installed. $\n$\nClick OK to remove the previous version or Cancel to cancel this upgrade." \
        IDOK uninst
    Abort

    uninst:
        ClearErrors
        ExecWait '$0 _?=$INSTDIR'

        IfErrors no_remove_uninstaller done
        no_remove_uninstaller:

    done:
FunctionEnd