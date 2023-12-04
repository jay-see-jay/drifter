import OnboardingSteps from '@/app/onboarding/OnboardingSteps'
import Database from '@/lib/database'

export default async function Onboarding() {
	return (
		<ul
			className={[
				'grid',
				'gap-2',
			].join(' ')}
		>
			{/*<OnboardingSteps*/}
			{/*	user={user}*/}
			{/*/>*/}
		</ul>
	)
}