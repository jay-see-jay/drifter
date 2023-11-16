import OnboardingStep from '@/app/onboarding/step'
import { currentUser } from '@clerk/nextjs'
import { redirect } from 'next/navigation'

const steps = [
	'Creating your account',
	'Syncing with Gmail',
	'Subscribing to new emails'
]

export type StepStatus = 'pending' | 'in_progress' | 'complete'

type StepsState = Map<number, StepStatus>

function initialiseState(): StepsState {
	const map: Map<number, StepStatus> = new Map()
	steps.forEach((step, index) => {
		map.set(index, 'pending')
	})
	return map
}

const stepsStatus = initialiseState()

export default async function Onboarding() {
	const user = await currentUser()
	if (! user) redirect('/')

	
	
	return (
		<ul
			className={[
				'grid',
				'gap-2',
			].join(' ')}
		>
			{steps.map((step, index) => {
				return <OnboardingStep key={index} step={step} status={stepsStatus.get(index)} />
			})}
		</ul>
	)
}