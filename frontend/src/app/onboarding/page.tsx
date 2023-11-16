import OnboardingStep from '@/app/onboarding/step';

const steps = [
	'Creating your account',
	'Syncing with Gmail',
	'Subscribing to new emails'
]

export default function Onboarding() {
	return (
		<ul
			className={[
				'grid',
				'gap-2',
			].join(' ')}
		>
			{steps.map((step, index) => {
				return <OnboardingStep key={index} step={step} />
			})}
		</ul>
	)
}