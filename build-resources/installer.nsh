; Custom NSIS installer script for Ideal Goggles
; This script enhances the installer with custom pages, messages, and behavior

!macro customHeader
  ; Custom installer header
  !define MUI_HEADERIMAGE
  !define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\nsis3-metro.bmp"
  !define MUI_HEADERIMAGE_RIGHT

  ; Custom welcome and finish pages
  !define MUI_WELCOMEFINISHPAGE_BITMAP "${BUILD_RESOURCES_DIR}\installer-sidebar.bmp"

  ; Custom text
  !define MUI_WELCOMEPAGE_TITLE "Welcome to Ideal Goggles Setup"
  !define MUI_WELCOMEPAGE_TEXT "This wizard will guide you through the installation of Ideal Goggles.$\r$\n$\r$\nIdeal Goggles is a privacy-focused local photo search and organization tool with AI capabilities.$\r$\n$\r$\nClick Next to continue."

  !define MUI_FINISHPAGE_TITLE "Installation Complete"
  !define MUI_FINISHPAGE_TEXT "Ideal Goggles has been successfully installed on your computer.$\r$\n$\r$\nClick Finish to close this wizard."
  !define MUI_FINISHPAGE_RUN "$INSTDIR\${APP_EXECUTABLE_FILENAME}"
  !define MUI_FINISHPAGE_RUN_TEXT "Launch Ideal Goggles"

  ; Show details by default
  ShowInstDetails show
  ShowUnInstDetails show
!macroend

!macro customInstall
  ; Custom installation steps
  DetailPrint "Installing Ideal Goggles..."

  ; Create additional shortcuts
  CreateShortCut "$DESKTOP\Ideal Goggles.lnk" "$INSTDIR\${APP_EXECUTABLE_FILENAME}" "" "$INSTDIR\${APP_EXECUTABLE_FILENAME}" 0

  ; Set file associations (if needed in future)
  ; WriteRegStr HKCR ".jpg" "" "IdealGoggles.Image"

  DetailPrint "Installation complete!"
!macroend

!macro customUnInstall
  ; Custom uninstallation steps
  DetailPrint "Uninstalling Ideal Goggles..."

  ; Remove desktop shortcut
  Delete "$DESKTOP\Ideal Goggles.lnk"

  ; Clean up registry (if any custom entries were added)
  ; DeleteRegKey HKCR "IdealGoggles.Image"

  ; Ask user if they want to keep their data
  MessageBox MB_YESNO|MB_ICONQUESTION "Do you want to keep your photo library data and settings?$\r$\n$\r$\nClick 'Yes' to keep your data for future installations.$\r$\nClick 'No' to completely remove all data." IDYES KeepData

  ; Remove user data if user chose to
  DetailPrint "Removing user data..."
  RMDir /r "$APPDATA\ideal-goggles"
  RMDir /r "$LOCALAPPDATA\ideal-goggles"

  KeepData:
  DetailPrint "Uninstallation complete!"
!macroend

!macro customInit
  ; Custom initialization before installation
  DetailPrint "Initializing Ideal Goggles Setup..."

  ; Check if app is running and prompt to close it
  FindWindow $0 "" "Ideal Goggles"
  StrCmp $0 0 notRunning
    MessageBox MB_OKCANCEL|MB_ICONEXCLAMATION "Ideal Goggles is currently running.$\r$\n$\r$\nPlease close it before continuing the installation." IDOK notRunning
    Quit
  notRunning:

  DetailPrint "System check complete."
!macroend

; Custom messages
!macro customInstallMode
  ; Set custom install mode messages
  ; This will be called when the installer starts
!macroend

; Installer attributes
!macro customInstallerAttribute
  ; Set custom attributes
  BrandingText "Ideal Goggles Team"

  ; Request admin privileges only if needed
  RequestExecutionLevel user
!macroend
