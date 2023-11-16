import MoreHoriz from '@/components/icons/MoreHoriz'
import Done from '@/components/icons/Done'
import ProgressActivity from '@/components/icons/ProgressActivity';

type OnboardingStepProps = {
	step: string
}

export default function OnboardingStep({ step }: OnboardingStepProps) {
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
			<MoreHoriz />
			<ProgressActivity />
			<Done />
			<li
				className={['text-xl'].join(' ')}
			>
				{step}
			</li>
		</div>
		)
}