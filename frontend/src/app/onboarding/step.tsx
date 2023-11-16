import MoreHoriz from '@/components/icons/moreHoriz'

type OnboardingStepProps = {
	step: string
}

export default function OnboardingStep({ step }: OnboardingStepProps) {
	return (
		<>
			<MoreHoriz />
			<li>{step}</li>
		</>
		)
}