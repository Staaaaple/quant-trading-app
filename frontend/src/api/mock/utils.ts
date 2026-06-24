/**
 * Mock API utility functions
 */

export function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

export function randomId(prefix = 'demo'): string {
  return `${prefix}_${Math.random().toString(36).substring(2, 9)}_${Date.now()}`
}

export function today(): string {
  return new Date().toISOString().split('T')[0]
}

export function now(): string {
  return new Date().toISOString()
}
