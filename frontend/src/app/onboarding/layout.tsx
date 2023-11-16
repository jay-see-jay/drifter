export default function OnboardingLayout({
	children,
}: {
	children: React.ReactNode
}) {
	
	const classes = [
		'h-full',
		'ml-[33%]',
		'flex',
		'items-center'
	]
	
	return (
		<section className={classes.join(' ')}>
			{children}
		</section>
	)
}