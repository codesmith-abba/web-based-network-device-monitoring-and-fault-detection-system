import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { ActivityIcon } from '../components/icons'
import { useAuth } from '../auth/useAuth'
import { AuthError } from '../auth/types'

function getNextPath() {
  const next = new URLSearchParams(window.location.search).get('next')
  return next?.startsWith('/') && !next.startsWith('//') ? next : '/'
}

export function LoginPage() {
  const { login, isAuthenticated, isLoading } = useAuth()
  const [identifier, setIdentifier] = useState('')
  const [password, setPassword] = useState('')
  const [identifierError, setIdentifierError] = useState('')
  const [passwordError, setPasswordError] = useState('')
  const [submitError, setSubmitError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (!isLoading && isAuthenticated) window.location.replace(getNextPath())
  }, [isAuthenticated, isLoading])

  const validate = () => {
    const nextIdentifierError = identifier.trim() ? '' : 'Username or email is required.'
    const nextPasswordError = password ? '' : 'Password is required.'
    setIdentifierError(nextIdentifierError)
    setPasswordError(nextPasswordError)
    return !nextIdentifierError && !nextPasswordError
  }

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSubmitError('')
    if (!validate()) return

    setIsSubmitting(true)
    try {
      await login({ identifier: identifier.trim(), password })
      window.location.replace(getNextPath())
    } catch (error) {
      if (error instanceof AuthError) {
        setSubmitError(error.message)
      } else {
        setSubmitError('We could not complete sign in. Please try again.')
      }
    } finally {
      setIsSubmitting(false)
    }
  }

  if (isLoading || isAuthenticated) {
    return (
      <main className="grid min-h-screen place-items-center bg-slate-50" aria-live="polite">
        <div className="size-8 animate-spin rounded-full border-2 border-slate-300 border-t-slate-950" aria-hidden="true" />
      </main>
    )
  }

  return (
    <main className="min-h-screen bg-slate-50 px-4 py-8 sm:px-6 sm:py-12">
      <div className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-md items-center justify-center">
        <section className="w-full rounded-3xl border border-slate-200 bg-white p-6 shadow-xl shadow-slate-950/[0.04] sm:p-8" aria-labelledby="login-title">
          <div className="mb-8 text-center">
            <div className="mx-auto mb-5 grid size-12 place-items-center rounded-2xl bg-slate-950 text-white shadow-sm">
              <ActivityIcon className="size-6" />
            </div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">NetWatch</p>
            <h1 id="login-title" className="mt-2 text-2xl font-semibold tracking-tight text-slate-950">Administrator sign in</h1>
            <p className="mt-2 text-sm leading-6 text-slate-500">Sign in to access the network monitoring workspace.</p>
          </div>

          {submitError && <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-800" role="alert">{submitError}</div>}

          <form className="space-y-5" onSubmit={handleSubmit} noValidate>
            <div>
              <label htmlFor="identifier" className="block text-sm font-medium text-slate-800">Username or email</label>
              <input id="identifier" name="identifier" type="text" autoComplete="username" value={identifier} onChange={(event) => setIdentifier(event.target.value)} aria-invalid={Boolean(identifierError)} aria-describedby={identifierError ? 'identifier-error' : undefined} className="mt-2 block w-full rounded-xl border border-slate-300 bg-white px-3.5 py-3 text-sm text-slate-950 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-slate-950 focus:ring-2 focus:ring-slate-950/10" placeholder="Enter your username or email" disabled={isSubmitting} />
              {identifierError && <p id="identifier-error" className="mt-2 text-xs text-red-700">{identifierError}</p>}
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-slate-800">Password</label>
              <input id="password" name="password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} aria-invalid={Boolean(passwordError)} aria-describedby={passwordError ? 'password-error' : undefined} className="mt-2 block w-full rounded-xl border border-slate-300 bg-white px-3.5 py-3 text-sm text-slate-950 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-slate-950 focus:ring-2 focus:ring-slate-950/10" placeholder="Enter your password" disabled={isSubmitting} />
              {passwordError && <p id="password-error" className="mt-2 text-xs text-red-700">{passwordError}</p>}
            </div>

            <button type="submit" disabled={isSubmitting} className="flex w-full items-center justify-center rounded-xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-60">
              {isSubmitting ? <><span className="mr-2 size-4 animate-spin rounded-full border-2 border-white/30 border-t-white" aria-hidden="true" />Signing in…</> : 'Sign in'}
            </button>
          </form>

          <p className="mt-6 text-center text-xs leading-5 text-slate-400">Administrator access only. Authentication is provided by the system backend when connected.</p>
        </section>
      </div>
    </main>
  )
}
