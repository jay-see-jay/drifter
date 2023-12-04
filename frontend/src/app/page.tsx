import SignUp from '@/app/SignUp'

export default function Home() {
    return (
        <main className="grid gap-y-4">
            <h1 className="text-xl font-bold">DR'FT'R</h1>
            <p>Drafts for your emails, written by AI.</p>
            <SignUp />
        </main>
    )
}
