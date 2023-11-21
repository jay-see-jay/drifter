import MoreHoriz from '@/components/icons/MoreHoriz'
import Done from '@/components/icons/Done'
import Close from '@/components/icons/Close'
import ProgressActivity from '@/components/icons/ProgressActivity'
import { StepStatus, Step, StepsDispatchAction } from '@/app/onboarding/OnboardingSteps'
import { useEffect, useTransition, Dispatch } from 'react';


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
	stepIndex: number
	status?: StepStatus
	userId: number
	updateStepStatus: Dispatch<StepsDispatchAction>
}

export default function OnboardingStep({
	step,
	stepIndex,
	status = 'pending',
	userId,
	updateStepStatus,
}: OnboardingStepProps) {
	const [isPending, startTransition] = useTransition()

	const isInProgress = status === 'in_progress'

	useEffect(() => {
		if (isInProgress && step.hasData === undefined && ! isPending) {
			startTransition(async () => {
				if (! step.action) {
					updateStepStatus({
						type: 'update',
						payload: {
							step: stepIndex,
							hasData: true
						}
					})
					return
				}
				const hasData = await step.action(userId)
				updateStepStatus({
					type: 'update',
					payload: {
						step: stepIndex,
						hasData,
					}
				})
			})
		}
	}, [status, stepIndex, updateStepStatus, isPending, isInProgress, step, userId])

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
			{getIcon(status, step.hasData)}
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