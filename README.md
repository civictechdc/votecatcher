# VoteCatcher ✓

**Open Source Campaign Infrastructure**

Automate ballot signature recognition and validation. Put powerful organizing tools in the hands of grassroots campaigns. Democracy should be accessible to everyone.

## 🚀 Features

- **Signature Validation**: High-accuracy signature triaging using multimodal LLMs integrated with voter files
- **Grassroots Focused**: Built for community organizers and campaigns that need powerful tools without the high costs
- **Open Source**: Transparent, community-driven technology that strengthens democratic participation
- **PDF Processing**: OCR capabilities for processing petition documents
- **Fuzzy Matching**: Advanced name and address matching algorithms
- **Campaign Management**: Multi-campaign support with user isolation

## 🛠️ Tech Stack

- **Frontend**: Next.js 15, React 19, TypeScript, Tailwind CSS
- **Backend**: Supabase (PostgreSQL, Auth, Storage, Edge Functions)
- **AI/ML**: OpenAI, Mistral, Gemini API integration
- **PDF Processing**: PDF.js for client-side PDF handling
- **UI Components**: Radix UI, Lucide React icons

<a id="prerequisites"></a>

## 📋 Prerequisites

Before deploying VoteCatcher, ensure you have:

- [Node.js](https://nodejs.org/en/download) 18+ installed
- [Supabase CLI](https://supabase.com/docs/guides/local-development) installed
- API keys for AI providers (OpenAI, Mistral, or Gemini)

## 🚀 Deployment Guide

The key objectives of this guide are to:

- Clone and set-up the VoteCatcher project
- Create and connect to the Supabase project
- Configure and run the Votecatcher application locally or deploy to the web.

This guide assumes you are using a Unix-like operating system (e.g. Linux, macOS). For Windows, make adjustments as necessary.

### 1. Clone and Setup

1. Clone the repository to your local machine:

```shell
git clone https://github.com/civictechdc/votecatcher
```

2. Open your terminal and navigate to the cloned project directory:

```shell
cd votecatcher
```

3. Install project dependencies

```shell
npm install
```

### 2. Supabase Setup

Quick setup run the `setupSupabase.sh` script

```sh
supabase login YOUR_SUPABASE_ACCESS_TOKEN
chmod +x setupSupabase.sh
./setupSupabase.sh
```

#### Create Supabase Project

1. Sign in or create an account at [supabase.com](https://supabase.com/dashboard/sign-up)
2. [Create a new project](https://supabase.com/dashboard/new) or select an existing one.
3. Locate your API key and project URL in the project dashboard under _Project Overview_. (You will need both for configuration.)
4. Log in to Supabase using the API key:

```shell
supabase login YOUR_SUPABASE_ACCESS_TOKEN
```

### 3. Database Migration

1. Open your terminal or file browser and navigate to the [supabase directory](https://github.com/civictechdc/votecatcher/tree/main/supabase) in your cloned project.
2. Confirm the following numbered SQL migration files are in the `supabase` directory:

   - [`1. campaign-schema.sql`](https://github.com/civictechdc/votecatcher/blob/main/supabase/1.%20campaign-schema.sql)
   - [`2. api-keys-schema.sql`](https://github.com/civictechdc/votecatcher/blob/main/supabase/2.%20api-keys-schema.sql)
   - [`3. voter-records-schema.sql`](https://github.com/civictechdc/votecatcher/blob/main/supabase/3.%20voter-records-schema.sql)
   - [`4. registered-voters.sql`](https://github.com/civictechdc/votecatcher/blob/main/supabase/4.%20registered-voters.sql)
   - [`5. fuzzy-matching-schema.sql`](https://github.com/civictechdc/votecatcher/blob/main/supabase/5.%20fuzzy-matching-schema.sql)

3. Run DB migrations. Enter the DB password when prompted

```shell
supabase db push
```

### 4. Deploy [Edge Functions](https://supabase.com/docs/guides/functions)

1. Deploy the Edge Functions:

```shell
supabase functions deploy process-voter-file
```

2. Select the desired project when prompted in the terminal.

3. Verify the edge function is deployed successfully by checking the list of functions:

```shell
supabase functions list
```
This should return a table with a `STATUS` column indicating the functions are deployed and active.

### 5. Environment Configuration

1. In your terminal, navigate to the root project folder.
2. Copy and rename the example `.env.local` file with either off the following commands:

```shell
cp .env.example.local .env.local
```

3. Open `.env.local` and fill in the required environment variables with the values collected in section [2. Supabase Setup](#2-supabase-setup):

```shell
# Required for Supabase
NEXT_PUBLIC_SUPABASE_URL=https://<project-id>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<public anon key>
# Required for encryption. Generate a secure 32-character hex string
ENCRYPTION_KEY=0123456789abcdef0123456789abcdef
```

**Note:** Environment variables with working defaults not shown. Open the `.env.local` file to view and modify as needed.

4. Save and close the `.env.local` file.

### 6. Storage Buckets Setup

The application automatically creates these storage buckets:

- `petitions` - For petition PDF files
- `voter-files` - For voter registration CSV files

Verify these buckets exist in your Supabase project under: _Storage > All Buckets_.

### 7. Run Locally for Development

1. In your terminal, navigate to the project root directory.
2. Start the development server:

```shell
npm run dev
```

3. Open your web browser and go to [http://localhost:3000](http://localhost:3000) to see the application.

### 8. Deploy to Web

#### Option A: Vercel (Recommended)

1. Push your code to GitHub
2. Connect your repository to [Vercel](https://vercel.com)
3. Add environment variables in Vercel dashboard
4. Deploy

#### Option B: Other Platforms

1. Build the application:

```shell
npm run build
```

2. Start production server:

```shell
npm start
```

## 🔧 Configuration

### Authentication

VoteCatcher uses Supabase Auth. Configure authentication providers in your Supabase dashboard:

1. Go to Authentication > Settings
2. Configure your preferred providers (Email, Google, etc.)

### Row Level Security (RLS)

All tables have RLS enabled with policies that ensure:

- Users can only access data from campaigns they own
- Proper data isolation between campaigns
- Secure API key management
- No service role access - all operations use user authentication

### API Key Management

Users can store their own API keys for AI providers:

- OpenAI API Key
- Mistral API Key
- Gemini API Key

Keys are encrypted and stored securely with user-level access control.

## 📁 Project Structure

```
votecatcher/
├── app/                    # Next.js App Router
│   ├── api/               # API routes
│   ├── auth/              # Authentication pages
│   ├── workspace/         # Main application workspace
│   └── globals.css        # Global styles
├── components/            # Reusable UI components
│   └── ui/               # Radix UI components
├── lib/                   # Utility libraries
│   ├── supabase/         # Supabase client configuration
│   ├── encryption.ts     # Encryption utilities
│   └── hooks/            # Custom React hooks
├── supabase/             # Database and functions
│   ├── functions/        # Edge functions
│   └── *.sql            # Database schemas
└── types/                # TypeScript type definitions
```

## 🔒 Security Features

- **Row Level Security**: All data is protected by RLS policies
- **Encrypted API Keys**: User API keys are encrypted at rest
- **User Isolation**: Campaigns are isolated by user ownership
- **Secure File Upload**: Files are stored in private buckets with access controls
- **User-Based Authentication**: All API operations use authenticated user context
- **No Service Role Access**: Eliminated service role key dependency for enhanced security

## 📄 License

This project is open source. See [LICENSE](LICENSE) for details.
