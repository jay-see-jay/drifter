import MoreHoriz from '@/components/icons/MoreHoriz'
import Done from '@/components/icons/Done'
import Close from '@/components/icons/Close'
import ProgressActivity from '@/components/icons/ProgressActivity'
import { StepStatus, Step } from '@/app/onboarding/OnboardingSteps'
import { useEffect, useState, useTransition } from 'react';


function getIcon(status: StepStatus, hasData?: boolean) {
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

type OnboardingStepProps = {
	step: Step
	status?: StepStatus
	userId: number
}

export default function OnboardingStep({
	step,
	status = 'pending',
	userId,
}: OnboardingStepProps) {
	const [hasData, setHasData] = useState<boolean | undefined>(undefined)
	const [isPending, startTransition] = useTransition()

	const isInProgress = status === 'in_progress'

	useEffect(() => {
		if (isInProgress && hasData === undefined && ! isPending) {
			startTransition(async () => {
				if (! step.action) {
					setHasData(Boolean(userId))
					return
				}
				const data = await step.action(userId)
				setHasData(data)
			})
		}
	}, [status, hasData, isPending, isInProgress, step, userId])

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
				className={[
					'text-xl',
					status === 'pending' ? 'text-gray-500' : null,
				].join(' ')}
			>
				{step.description}
			</li>
		</div>
		)
}