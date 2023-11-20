import mysql, { RowDataPacket } from 'mysql2/promise'


type User = {
	
	email: string
}

export default class Database {
	initialized: boolean
	connection?: mysql.Connection
	
	INITIALIZATION_WARNING = 'Call .init() first!'
	
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
	
	async get_user(clerk_id: string): Promise<User> {
		if (! this.initialized) {
			await this.init()
		}
		
		const allColumns = [
			'email',
		]
		
		const query = `SELECT ${allColumns.join(', ')} FROM users WHERE clerk_user_id = ?`
		const variables = [clerk_id]
		
		const [response] = await this.connection!.execute(query, variables)
		
		if (Array.isArray(response)) {
		    return response[0] as Promise<User>
		} else {
			throw Error('Response from db was not array')
		}
	}
}