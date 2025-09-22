.PHONY: help frontend-install build-frontend build-electron-main build-electron package-backend dist-mac dist-win dist-all clean

PYTHON ?= python3
FRONTEND_PM ?= pnpm

help:
	@echo "Targets:"
	@echo "  frontend-install   Install frontend dependencies (uses FRONTEND_PM)"
	@echo "  build-frontend     Build React renderer (Vite)"
	@echo "  build-electron-main Compile Electron main/preload (tsc)"
	@echo "  build-electron     Build renderer + main (no packaging)"
	@echo "  package-backend    Build backend binary via PyInstaller"
	@echo "  dist-mac           Build macOS DMG (packages backend first)"
	@echo "  dist-win           Build Windows NSIS (packages backend first)"
	@echo "  dist-all           Build installers for mac/win/linux"
	@echo "Variables:"
	@echo "  PYTHON=python3     Python interpreter for backend packaging"
	@echo "  FRONTEND_PM=pnpm   Package manager for frontend (pnpm or npm)"

frontend-install:
	cd frontend && $(FRONTEND_PM) install --no-optional || true

build-frontend:
	cd frontend && $(FRONTEND_PM) run build

build-electron-main:
	cd frontend && npx --no-install tsc -p electron/tsconfig.json

build-electron: build-frontend build-electron-main

package-backend:
	$(MAKE) -C backend package PYTHON=$(PYTHON)

dist-mac: package-backend build-electron
	cd frontend && npx --no-install electron-builder -- --mac

dist-win: package-backend build-electron
	cd frontend && npx --no-install electron-builder -- --win

dist-all: package-backend build-electron
	cd frontend && npx --no-install electron-builder -- -mwl

clean:
	$(MAKE) -C backend clean || true
	rm -rf frontend/dist frontend/dist-electron frontend/electron/dist || true
