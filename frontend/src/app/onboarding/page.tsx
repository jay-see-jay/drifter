import OnboardingSteps from '@/app/onboarding/OnboardingSteps'
import { currentUser } from '@clerk/nextjs'
import { redirect } from 'next/navigation'
import Database from '@/lib/database'

const db = new Database()

export default async function Onboarding() {
	const clerkUser = await currentUser()
	if (! clerkUser) redirect('/')
	const user = await db.getUser(clerkUser.id)
	const messageHeader = await db.getMessageHeader(user)
	
	return (
		<ul
			className={[
				'grid',
				'gap-2',
			].join(' ')}
		>
			<OnboardingSteps
				userEmail={Boolean(user.email)}
				messageHeaderId={Boolean(messageHeader.message_id)}
				latestHistoryId={true}
			/>
		</ul>
	)
}