'use client'
import { Button } from '@/components/ui/button'
import { MouseEvent } from 'react'
import { createBrowserClient } from '@supabase/ssr'
import Google from '@/components/icons/Google'


const supabase = createBrowserClient(
	process.env.NEXT_PUBLIC_SUPABASE_URL!,
	process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)

async function handleClick(e: MouseEvent) {
    await supabase.auth.signInWithOAuth({
        provider: 'google',
        options: {
            redirectTo: 'http://localhost:3000/auth/callback?next=/onboarding',
        },
    })
}

export default function SignUp() {
	
    return (
        <Button
            onClick={handleClick}
            className={[
                'inline-flex',
                'gap-x-2',
                'w-min',
            ].join(' ')}
            variant='secondary'
        >
            <Google classes={['w-4']} />
			Continue with Google
        </Button>
    )
}