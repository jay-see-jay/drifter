from typing import TypedDict, Literal, List


class Verification(TypedDict):
    attempts: int
    status: str
    strategy: str


class WalletVerification(Verification):
    expire_at: int
    nonce: str


class UserWallet(TypedDict):
    id: str
    object: str
    verification: WalletVerification
    web3_wallet: str


class UserPhoneNumber(TypedDict):
    default_second_factor: bool
    id: str
    linked_to: List[str]
    object: str
    phone_number: str
    reserved_for_second_factor: bool
    verification: Verification


class UserEmailAddress(TypedDict):
    email_address: str
    id: str
    linked_to: List[str]
    object: Literal['email_address']
    verification: Verification


class UserCreatedEventData(TypedDict):
    birthday: str
    created_at: int
    email_addresses: List[UserEmailAddress]
    external_accounts: List[dict]
    external_id: str
    first_name: str
    gender: str
    id: str
    image_url: str
    last_name: str
    last_sign_in_at: int
    object: str
    password_enabled: bool
    phone_numbers: List[UserPhoneNumber]
    primary_email_address_id: str
    primary_phone_number_id: str
    primary_web3_wallet_id: str
    private_metadata: dict
    profile_image_url: str
    public_metadata: dict
    two_factor_enabled: bool
    unsafe_metadata: dict
    updated_at: int
    username: str
    web3_wallets: List[UserWallet]


class UserCreatedEvent(TypedDict):
    data: UserCreatedEventData
    object: Literal['event']
    type: Literal['user.created']
