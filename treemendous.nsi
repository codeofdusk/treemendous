;-------------------------------------------------------------------------------
; Includes
!include "MUI2.nsh"
!include "LogicLib.nsh"
!include "WinVer.nsh"
!include "x64.nsh"

;-------------------------------------------------------------------------------
; Constants
!define PRODUCT_NAME "Treemendous"
!define PRODUCT_DESCRIPTION "An accessible tree creation and exploration tool especially designed for blind and vision impaired practitioners and students of linguistics and computer science."
!define COPYRIGHT "Copyright © 2021 Bill Dengler and open source contributors"
!define COMPANYNAME "Bill Dengler and open'source contributors"
!define PRODUCT_VERSION "1.0.1.0"
!define SETUP_VERSION 1.0.0.0

;-------------------------------------------------------------------------------
; Attributes
Name "Treemendous"
OutFile "TreemendousSetup.exe"
InstallDir "$PROGRAMFILES\Treemendous"
RequestExecutionLevel highest

;-------------------------------------------------------------------------------
; Version Info
VIProductVersion "${PRODUCT_VERSION}"
VIAddVersionKey "ProductName" "${PRODUCT_NAME}"
VIAddVersionKey "ProductVersion" "${PRODUCT_VERSION}"
VIAddVersionKey "FileDescription" "${PRODUCT_DESCRIPTION}"
VIAddVersionKey "LegalCopyright" "${COPYRIGHT}"
VIAddVersionKey "FileVersion" "${SETUP_VERSION}"

;-------------------------------------------------------------------------------
; Modern UI Appearance
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\orange-install.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Header\orange.bmp"
!define MUI_WELCOMEFINISHPAGE_BITMAP "${NSISDIR}\Contrib\Graphics\Wizard\orange.bmp"
!define MUI_FINISHPAGE_RUN "$INSTDIR\treemendous.exe"

;-------------------------------------------------------------------------------
; Installer Pages
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "copying.txt"
!insertmacro MUI_PAGE_COMPONENTS
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

;-------------------------------------------------------------------------------
; Uninstaller Pages
!insertmacro MUI_UNPAGE_WELCOME
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_FINISH

;-------------------------------------------------------------------------------
; Languages
!insertmacro MUI_LANGUAGE "English"

;-------------------------------------------------------------------------------
; Installer Sections
Section "Treemendous application" Treemendous
	SetOutPath $INSTDIR
	File /r "treemendous.dist\"
	;File "Readme.txt"
	WriteUninstaller "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Add Treemendous to start menu" StartMenuShortcuts
	CreateShortcut "$SMPROGRAMS\Treemendous.lnk" "$INSTDIR\treemendous.exe"
	CreateShortcut "$SMPROGRAMS\Uninstall Treemendous.lnk" "$INSTDIR\uninstall.exe"
SectionEnd

Section "Add Treemendous to desktop" DesktopShortcuts
	CreateShortcut "$DESKTOP\Treemendous.lnk" "$INSTDIR\treemendous.exe"
SectionEnd

Section "Associate *.treemendous trees with Treemendous" FileAssociations
	WriteRegStr HKCR ".treemendous" ""  "Treemendous"
	WriteRegStr HKCR "treemendous\shell\open\command" "" "$\"$INSTDIR\treemendous.exe$\" $\"%1$\""
SectionEnd

;-------------------------------------------------------------------------------
; Uninstaller Sections
Section "Uninstall"
	Delete "$INSTDIR\uninstall.exe"
	Delete "$SMPROGRAMS\Treemendous.lnk"
	Delete "$SMPROGRAMS\Uninstall Treemendous.lnk"
	Delete "$DESKTOP\Treemendous.lnk"
	Rmdir /r $INSTDIR
	DeleteRegKey HKCR ".treemendous"
	DeleteRegKey HKCR "treemendous\shell\open\command"
SectionEnd
