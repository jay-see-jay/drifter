import mysql from 'mysql2/promise'


type User = {
	pk: number
	email: string
}

type MessageHeader = {
	message_id: string
}

type HistoryRecord = {
	id: string
}

type QueryVariable = string | number

export default class Database {
	initialized: boolean
	connection?: mysql.Connection
	
	constructor() {
		this.initialized = false
	}
	
	async init() {
		this.connection = await mysql.createConnection({
			host: process.env.DATABASE_HOST,
			user: process.env.DATABASE_USERNAME_PROD,
			password: process.env.DATABASE_PASSWORD_PROD,
			database: process.env.DATABASE,
			ssl: {
				ca: process.env.CERTIFICATE_PATH
			}
		})
		this.initialized = true
	}
	
	async read<T>(query: string, variables: QueryVariable[]): Promise<T> {
		if (! this.initialized) {
			await this.init()
		}

		const [response] = await this.connection!.execute(query, variables)

		if (Array.isArray(response)) {
			return response[0] as Promise<T>
		} else {
			throw Error('Response from db was not array')
		}
	}

	async getUser(clerk_id: string): Promise<User> {
		const allColumns = [ 'pk', 'email' ]

		const query = `SELECT ${allColumns.join(', ')} FROM users WHERE clerk_user_id = ?`
		const variables = [clerk_id]

		return this.read<User>(query, variables)
	}

	async getMessageHeader(user: User) {
		const allColumns = [ 'message_id' ]
		const query = `SELECT ${allColumns.join(', ')} FROM message_headers WHERE user_pk = ? LIMIT 1`
		const variables = [user.pk]

		return this.read<MessageHeader>(query, variables)
	}

	async getHistoryId(user: User) {
		const allColumns = [ 'id' ]
		const query = `SELECT ${allColumns.join(', ')} FROM history WHERE user_pk = ? LIMIT 1`
		const variables = [user.pk]
		
		return this.read<HistoryRecord>(query, variables)
	}

}