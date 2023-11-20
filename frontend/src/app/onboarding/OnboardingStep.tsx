import MoreHoriz from '@/components/icons/MoreHoriz'
import Done from '@/components/icons/Done'
import ProgressActivity from '@/components/icons/ProgressActivity'
import { StepStatus } from '@/app/onboarding/OnboardingSteps'

type OnboardingStepProps = {
	step: string
	status?: StepStatus
}

function getIcon(status: StepStatus) {
	if (status === 'complete') return <Done />
	if (status === 'in_progress') return <ProgressActivity />
	return <MoreHoriz />
}

export default function OnboardingStep({
	step,
	status = 'pending',
}: OnboardingStepProps) {
	const divClasses = [
		'grid',
		'gap-2',
		'grid-flow-col',
		'auto-cols-max',
		'items-center'
	]

	return (
		<div
			className={divClasses.join(' ')}
		>
			{getIcon(status)}
			<li
				className={['text-xl'].join(' ')}
			>
				{step}
			</li>
		</div>
		)
}