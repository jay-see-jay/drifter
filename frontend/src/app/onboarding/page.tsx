import OnboardingSteps from '@/app/onboarding/OnboardingSteps'
import { currentUser } from '@clerk/nextjs'
import { redirect } from 'next/navigation'
import Database from '@/lib/database'

const db = new Database()

export default async function Onboarding() {
	const clerkUser = await currentUser()
	if (! clerkUser) redirect('/')
	const user = await db.get_user(clerkUser.id)
	
	return (
		<ul
			className={[
				'grid',
				'gap-2',
			].join(' ')}
		>
			<OnboardingSteps userEmail={user.email} />
		</ul>
	)
}