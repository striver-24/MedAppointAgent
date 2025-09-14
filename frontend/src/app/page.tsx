import Chat from "../components/Chat.tsx";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center bg-gray-100">
      <div className="w-full max-w-2xl flex-grow flex flex-col my-8 bg-white shadow-lg rounded-lg">
        <div className="bg-blue-600 text-white p-4 rounded-t-lg">
          <h1 className="text-xl font-bold">Medical Appointment Assistant</h1>
        </div>
        <Chat />
      </div>
    </main>
  );
}