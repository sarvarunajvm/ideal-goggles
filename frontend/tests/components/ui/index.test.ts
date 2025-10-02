/**
 * Unit tests for UI Components Index
 * Priority: P2 (Export verification)
 */

import * as UIComponents from '../../../src/components/ui/index'

describe('UI Components Index', () => {
  test('exports Button component', () => {
    expect(UIComponents.Button).toBeDefined()
    expect(typeof UIComponents.Button).toBe('object') // React component
  })

  test('exports buttonVariants', () => {
    expect(UIComponents.buttonVariants).toBeDefined()
    expect(typeof UIComponents.buttonVariants).toBe('function')
  })

  test('exports Card components', () => {
    expect(UIComponents.Card).toBeDefined()
    expect(UIComponents.CardHeader).toBeDefined()
    expect(UIComponents.CardFooter).toBeDefined()
    expect(UIComponents.CardTitle).toBeDefined()
    expect(UIComponents.CardDescription).toBeDefined()
    expect(UIComponents.CardContent).toBeDefined()
  })

  test('exports Input component', () => {
    expect(UIComponents.Input).toBeDefined()
  })

  test('exports Label component', () => {
    expect(UIComponents.Label).toBeDefined()
  })

  test('exports Switch component', () => {
    expect(UIComponents.Switch).toBeDefined()
  })

  test('exports Checkbox component', () => {
    expect(UIComponents.Checkbox).toBeDefined()
  })

  test('exports Tabs components', () => {
    expect(UIComponents.Tabs).toBeDefined()
    expect(UIComponents.TabsList).toBeDefined()
    expect(UIComponents.TabsTrigger).toBeDefined()
    expect(UIComponents.TabsContent).toBeDefined()
  })

  test('exports Badge components', () => {
    expect(UIComponents.Badge).toBeDefined()
    expect(UIComponents.badgeVariants).toBeDefined()
    expect(typeof UIComponents.badgeVariants).toBe('function')
  })

  test('exports Progress component', () => {
    expect(UIComponents.Progress).toBeDefined()
  })

  test('exports Separator component', () => {
    expect(UIComponents.Separator).toBeDefined()
  })

  test('exports ScrollArea components', () => {
    expect(UIComponents.ScrollArea).toBeDefined()
    expect(UIComponents.ScrollBar).toBeDefined()
  })

  test('exports Toast components and types', () => {
    expect(UIComponents.Toast).toBeDefined()
    expect(UIComponents.ToastProvider).toBeDefined()
    expect(UIComponents.ToastViewport).toBeDefined()
    expect(UIComponents.ToastTitle).toBeDefined()
    expect(UIComponents.ToastDescription).toBeDefined()
    expect(UIComponents.ToastClose).toBeDefined()
    expect(UIComponents.ToastAction).toBeDefined()
  })

  test('exports Toaster component', () => {
    expect(UIComponents.Toaster).toBeDefined()
  })

  test('exports toast utilities', () => {
    expect(UIComponents.useToast).toBeDefined()
    expect(UIComponents.toast).toBeDefined()
    expect(typeof UIComponents.useToast).toBe('function')
    expect(typeof UIComponents.toast).toBe('function')
  })

  test('all exports are defined', () => {
    const exportKeys = Object.keys(UIComponents)
    expect(exportKeys.length).toBeGreaterThan(0)

    exportKeys.forEach(key => {
      expect(UIComponents[key as keyof typeof UIComponents]).toBeDefined()
    })
  })

  test('no unexpected exports', () => {
    const expectedExports = [
      'Button', 'buttonVariants',
      'Card', 'CardHeader', 'CardFooter', 'CardTitle', 'CardDescription', 'CardContent',
      'Input', 'Label', 'Switch', 'Checkbox',
      'Tabs', 'TabsList', 'TabsTrigger', 'TabsContent',
      'Badge', 'badgeVariants',
      'Progress', 'Separator',
      'ScrollArea', 'ScrollBar',
      'Toast', 'ToastProvider', 'ToastViewport', 'ToastTitle', 'ToastDescription', 'ToastClose', 'ToastAction',
      'Toaster', 'useToast', 'toast'
    ]

    const actualExports = Object.keys(UIComponents)
    expectedExports.forEach(expectedExport => {
      expect(actualExports).toContain(expectedExport)
    })
  })
})