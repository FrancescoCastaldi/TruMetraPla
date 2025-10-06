; Script NSIS minimale per creare un installer di TruMetraPla

!define APP_NAME "TruMetraPla"
!define APP_VERSION "0.1.0"
!define APP_PUBLISHER "TruMetraPla"
!define INSTALL_DIR "$PROGRAMFILES64\${APP_NAME}"

SetCompressor /SOLID lzma

Name "${APP_NAME} ${APP_VERSION}"
OutFile "TruMetraPla_Setup_${APP_VERSION}.exe"
InstallDir "${INSTALL_DIR}"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "Install"
    SetOutPath "$INSTDIR"
    File /r "dist\TruMetraPla\*.*"

    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\TruMetraPla.exe"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}.lnk" "$INSTDIR\TruMetraPla.exe"
SectionEnd

Section "Uninstall"
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}.lnk"
    Delete /REBOOTOK "$INSTDIR\TruMetraPla.exe"
    RMDir /r "$INSTDIR"
SectionEnd
