import { defineEventHandler, getCookie, getRequestURL, sendRedirect, setHeader } from 'h3'
import { AUTH_COOKIE_NAME } from '../utils/auth'

export default defineEventHandler((event) => {
  if (getRequestURL(event).pathname !== '/') return

  // Never cache a response whose destination depends on the user's session.
  setHeader(event, 'Cache-Control', 'private, no-store')

  // Redirect before SSR so the browser receives the auth layout on first load.
  // A present cookie is still validated by the existing authentication flow.
  if (!getCookie(event, AUTH_COOKIE_NAME)) {
    return sendRedirect(event, '/login', 302)
  }
})
