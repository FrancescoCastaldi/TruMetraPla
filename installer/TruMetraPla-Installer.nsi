; Script NSIS per creare un installer di TruMetraPla con pagina di benvenuto moderna

!include "MUI2.nsh"

!ifndef APP_NAME
!define APP_NAME "TruMetraPla"
!endif
!ifndef APP_VERSION
!define APP_VERSION "0.1.0"
!endif
!ifndef APP_PUBLISHER
!define APP_PUBLISHER "TruMetraPla"
!endif
!ifndef INSTALL_DIR
!define INSTALL_DIR "C:\\TruMetraPla"
!endif
!ifndef INPUT_EXE
!define INPUT_EXE "dist\\TruMetraPla.exe"
!endif
!ifndef OUTPUT_FILE
!define OUTPUT_FILE "TruMetraPla_Setup_${APP_VERSION}.exe"
!endif

SetCompressor /SOLID lzma

Name "${APP_NAME} ${APP_VERSION}"
OutFile "${OUTPUT_FILE}"
InstallDir "${INSTALL_DIR}"
InstallDirRegKey HKLM "Software\${APP_NAME}" "Install_Dir"
RequestExecutionLevel admin

!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\\Contrib\\Graphics\\Icons\\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\\Contrib\\Graphics\\Icons\\modern-uninstall.ico"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

!insertmacro MUI_LANGUAGE "Italian"

Section "Install"
    SetOutPath "$INSTDIR"
    File "/oname=TruMetraPla.exe" "${INPUT_EXE}"

    WriteRegStr HKLM "Software\${APP_NAME}" "Install_Dir" "$INSTDIR"
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\TruMetraPla.exe"
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\TruMetraPla.exe"
SectionEnd

Section "Uninstall"
    Delete "$DESKTOP\${APP_NAME}.lnk"
    Delete "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    Delete /REBOOTOK "$INSTDIR\TruMetraPla.exe"
    RMDir /r "$INSTDIR"
    DeleteRegKey HKLM "Software\${APP_NAME}"
SectionEnd
