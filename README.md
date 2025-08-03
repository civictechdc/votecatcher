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

## 📋 Prerequisites

Before deploying VoteCatcher, ensure you have:

- [Node.js](https://nodejs.org/) 18+ installed
- [Supabase CLI](https://supabase.com/docs/guides/local-development) installed
- API keys for AI providers (OpenAI, Mistral, or Gemini)

## 🚀 Deployment Guide

### 1. Clone and Setup

```bash
git clone https://github.com/civictechdc/votecatcher
cd votecatcher
npm install
```

### 2. Supabase Setup

#### Create Supabase Project

1. Sign in or create an account at [supabase.com](https://supabase.com/dashboard/sign-up)
2. [Create a new project](https://supabase.com/dashboard/new) or select an existing one.
3. Locate your API key and project URL in the project dashboard under 'Project Overview'. (You will need both for configuration.)

### 3. Database Migration

1. Open your terminal or file browser and navigate to the [supabase directory](https://github.com/civictechdc/votecatcher/tree/main/supabase) in your cloned project.
2. Confirm the following numbered SQL migration files are in the `supabase` directory:

   - [`1. campaign-schema.sql`](https://github.com/civictechdc/votecatcher/blob/main/supabase/1.%20campaign-schema.sql)
   - [`2. api-keys-schema.sql`](https://github.com/civictechdc/votecatcher/blob/main/supabase/2.%20api-keys-schema.sql)
   - [`3. voter-records-schema.sql`](https://github.com/civictechdc/votecatcher/blob/main/supabase/3.%20voter-records-schema.sql)
   - [`4. registered-voters.sql`](https://github.com/civictechdc/votecatcher/blob/main/supabase/4.%20registered-voters.sql)
   - [`5. fuzzy-matching-schema.sql`](https://github.com/civictechdc/votecatcher/blob/main/supabase/5.%20fuzzy-matching-schema.sql)

3. In your web browser, open your [Supabase project dashboard](https://supabase.com/dashboard), navigate to the 'SQL Editor'.
4. For each SQL file:
   - Open and copy the contents
   - In the Supabase SQL editor, open a new tab
   - Paste the copied contents
   - Press the 'Run' button to execute the script.

Note: It is critical you **copy and run the scripts in the ascending numbered order listed above**.

5. Verify no errors occurred during the execution of the scripts. You should see a success message for each script in the SQL editor.

### 4. Deploy Edge Functions

1. Install the Supabase CLI [if you haven't already](https://github.com/civictechdc/votecatcher/tree/main?tab=readme-ov-file#-prerequisites)
2. In your terminal, navigate to the project root directory
3. Log in to Supabase:

```shell
# Use the API key provided in your Supabase project dashboard
supabase login YOUR_SUPABASE_ACCESS_TOKEN
```

4. Follow the prompts to authenticate your Supabase account.

5. Deploy the Edge Functions:

```shell
supabase functions deploy process-voter-file
```

6. Select the desired project when prompted in the terminal.

7. Verify the edge function is deployed successfully by checking the list of functions:

```shell
supabase functions list
```

This should return a table with a 'STATUS' column indicating the functions are deployed and active.

### 5. Environment Configuration

1. In your terminal, navigate to the root project folder.
2. Copy and rename the example `.env.local` file with either off the following commands:

```shell
cp example.env.local .env.local
```

3. Open `.env.local` and fill in the required environment variables:

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

Verify these buckets exist in your Supabase project under Storage > Buckets.

### 7. Development

1. In your terminal, navigate to the project root directory.
2. Start the development server:

```shell
npm run dev
```

3. Open your web browser and go to [http://localhost:3000](http://localhost:3000) to see the application.

### 8. Production Deployment

#### Option A: Vercel (Recommended)

1. Push your code to GitHub
2. Connect your repository to [Vercel](https://vercel.com)
3. Add environment variables in Vercel dashboard
4. Deploy

#### Option B: Other Platforms

```bash
# Build the application
npm run build

# Start production server
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
