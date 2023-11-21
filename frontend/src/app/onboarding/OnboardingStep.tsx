import MoreHoriz from '@/components/icons/MoreHoriz'
import Done from '@/components/icons/Done'
import Close from '@/components/icons/Close'
import ProgressActivity from '@/components/icons/ProgressActivity'
import { StepStatus } from '@/app/onboarding/OnboardingSteps'

type OnboardingStepProps = {
	step: { action: string, dataRequired: string }
	hasData: boolean
	status?: StepStatus
}

function getIcon(status: StepStatus, hasData: boolean) {
	if (status === 'complete') {
		if (hasData) {
			return <Done />
		} else {
			return <Close />
		}
	}
	if (status === 'in_progress') return <ProgressActivity />
	return <MoreHoriz />
}

export default function OnboardingStep({
	step,
	hasData,
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
			{getIcon(status, hasData)}
			<li
				className={['text-xl'].join(' ')}
			>
				{step.action}
			</li>
		</div>
		)
}