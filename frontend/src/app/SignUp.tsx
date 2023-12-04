'use client'
import { Button } from '@/components/ui/button'
import { MouseEvent } from 'react'
import Google from '@/components/icons/Google'
import useFirebase from '@/hooks/useFirebase'
import { signInWithPopup } from 'firebase/auth'

export default function SignUp() {
    const { auth, provider } = useFirebase()

    async function handleClick(e: MouseEvent) {
	    try {
		    const result = await signInWithPopup(auth, provider)
	        console.log('result', result)
	    } catch (err) {
	        console.log(err)
	    }
    }
	
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