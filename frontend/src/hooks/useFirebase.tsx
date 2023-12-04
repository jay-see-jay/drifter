'use client'

import { initializeApp } from 'firebase/app'
import { getAuth, GoogleAuthProvider } from 'firebase/auth'

const firebaseConfig = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY,
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN,
    projectId: process.env.NEXT_PUBLIC_GOOGLE_PROJECT_ID,
}

const app = initializeApp(firebaseConfig)

const auth = getAuth(app)

const provider = new GoogleAuthProvider()
provider.setCustomParameters({
    access_type: 'offline',
    prompt: 'consent',
})
const SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
]

SCOPES.forEach(scope => provider.addScope(scope))

export default function useFirebase() {
    return { auth, provider }
}