import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { DocumentItem } from '../types';
import {
  Upload,
  Search,
  FileText,
  Trash2,
  ExternalLink,
  X,
  Copy,
  Check,
  Clock,
  CheckCircle2,
  AlertCircle,
  FileCode,
  Filter
} from 'lucide-react';

export const KnowledgePage: React.FC = () => {
  const {
    documents,
    previewDocument,
    setPreviewDocument,
    uploadDocument,
    deleteDocument
  } = useApp();

  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'ready' | 'processing'>('all');
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'preview' | 'citations' | 'details'>('preview');
  const [copiedCitation, setCopiedCitation] = useState(false);

  // New upload form
  const [uploadName, setUploadName] = useState('');
  const [uploadType, setUploadType] = useState<'PDF' | 'MD' | 'DOCX' | 'TXT'>('PDF');

  const filteredDocs = documents.filter(doc => {
    const matchesSearch = doc.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                          doc.scope.toLowerCase().includes(searchQuery.toLowerCase());
    if (statusFilter === 'ready') return matchesSearch && doc.status === 'indexed';
    if (statusFilter === 'processing') return matchesSearch && doc.status === 'processing';
    return matchesSearch;
  });

  const handleUploadSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (uploadName.trim()) {
      uploadDocument(uploadName, uploadType, '2.4 MB');
      setUploadName('');
      setIsUploadModalOpen(false);
    }
  };

  const handleCopyCitation = () => {
    if (previewDocument) {
      navigator.clipboard.writeText(
        `[${previewDocument.name}, Page 12, Section 1.1 The Java Platform]`
      );
      setCopiedCitation(true);
      setTimeout(() => setCopiedCitation(false), 2000);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-[#18110c] text-[#fbf8f2] overflow-y-auto">
      {/* Top Header */}
      <div className="p-8 border-b border-[#302016] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white tracking-tight">Knowledge</h1>
          <p className="text-xs text-[#a08c7e] mt-1 max-w-xl leading-relaxed">
            Upload, organise and search your documents. NEXUS indexes your files locally into ChromaDB so agents can use them in reasoning and planning.
          </p>
        </div>

        <button
          onClick={() => setIsUploadModalOpen(true)}
          className="bg-[#f25c24] hover:bg-[#d94c17] text-white font-semibold text-xs px-5 py-3 rounded-xl shadow-lg shadow-[#f25c24]/20 flex items-center justify-center gap-2 self-start sm:self-auto transition-all"
        >
          <Upload className="w-4 h-4" />
          <span>Upload files</span>
        </button>
      </div>

      <div className="p-8 space-y-6 max-w-6xl">
        {/* Search & Filter Bar */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 text-[#8e7869] absolute left-3.5 top-1/2 -translate-y-1/2" />
            <input
              type="text"
              placeholder="Search documents by name or scope..."
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              className="w-full bg-[#241710] border border-[#3d291d] focus:border-[#f25c24] rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder-[#8e7869] focus:outline-none"
            />
          </div>

          {/* Filter Pills */}
          <div className="flex items-center gap-1.5 bg-[#241710] p-1 rounded-xl border border-[#3d291d] shrink-0">
            {(['all', 'ready', 'processing'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setStatusFilter(tab)}
                className={`text-xs px-4 py-1.5 rounded-lg font-medium capitalize transition-colors ${
                  statusFilter === tab
                    ? 'bg-[#f25c24] text-white'
                    : 'text-[#8e7869] hover:text-white'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Documents Table */}
        <div className="bg-[#22160f] border border-[#3b271d] rounded-2xl overflow-hidden shadow-sm">
          <table className="w-full text-left text-xs">
            <thead className="bg-[#1b120c] border-b border-[#3b271d] text-[#8e7869] uppercase font-bold text-[10px] tracking-wider">
              <tr>
                <th className="py-3 px-4">Name</th>
                <th className="py-3 px-4">Type</th>
                <th className="py-3 px-4">Pages</th>
                <th className="py-3 px-4">Scope</th>
                <th className="py-3 px-4">Index status</th>
                <th className="py-3 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#302016]">
              {filteredDocs.map(doc => (
                <tr
                  key={doc.id}
                  onClick={() => setPreviewDocument(doc)}
                  className="hover:bg-[#2b1c13] transition-colors cursor-pointer group"
                >
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2.5">
                      <div className="w-7 h-7 rounded-lg bg-[#301f15] text-[#f25c24] flex items-center justify-center font-bold text-[10px]">
                        {doc.type}
                      </div>
                      <span className="font-semibold text-white group-hover:text-[#f25c24] transition-colors">
                        {doc.name}
                      </span>
                    </div>
                  </td>
                  <td className="py-3 px-4 text-[#a08c7e] font-mono">{doc.type}</td>
                  <td className="py-3 px-4 text-[#a08c7e]">{doc.pages}</td>
                  <td className="py-3 px-4">
                    <span className="bg-[#301f15] text-[#d6c7bc] px-2 py-0.5 rounded border border-[#483325] text-[11px]">
                      {doc.scope}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    {doc.status === 'indexed' ? (
                      <span className="flex items-center gap-1.5 text-emerald-400 font-medium">
                        <span className="w-2 h-2 rounded-full bg-emerald-500" />
                        <span>Indexed</span>
                      </span>
                    ) : (
                      <span className="flex items-center gap-1.5 text-amber-400 font-medium">
                        <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse" />
                        <span>Processing</span>
                      </span>
                    )}
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      onClick={e => {
                        e.stopPropagation();
                        deleteDocument(doc.id);
                      }}
                      className="p-1.5 rounded-lg text-[#8e7869] hover:text-red-400 hover:bg-red-950/20 transition-colors"
                      title="Delete document and purge vectors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Document Detail Preview Drawer / Modal */}
        {previewDocument && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#fdfbf7] text-[#1e140f] border border-[#d8cbb8] rounded-3xl max-w-4xl w-full max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-fade-in">
              {/* Drawer Header */}
              <div className="p-5 border-b border-[#e4d9c7] flex items-center justify-between bg-[#f8f3eb]">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-[#f25c24] text-white flex items-center justify-center font-bold text-xs">
                    {previewDocument.type}
                  </div>
                  <div>
                    <h3 className="font-bold text-base text-[#1e140f] flex items-center gap-2">
                      <span>{previewDocument.name}</span>
                      <span className="text-xs bg-[#ede3d3] text-[#6b584d] px-2 py-0.5 rounded-full font-normal">
                        {previewDocument.pages} pages · {previewDocument.scope}
                      </span>
                    </h3>
                  </div>
                </div>

                <button
                  onClick={() => setPreviewDocument(null)}
                  className="p-1.5 rounded-full hover:bg-[#eadecc] text-[#786558] transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* Drawer Body - Split into Content & Citation preview */}
              <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Left 2 cols: Document content viewer */}
                <div className="md:col-span-2 space-y-4">
                  {/* Tabs */}
                  <div className="flex items-center gap-2 border-b border-[#e4d9c7] pb-2 text-xs font-semibold">
                    <button
                      onClick={() => setActiveTab('preview')}
                      className={`px-3 py-1 rounded-lg ${
                        activeTab === 'preview'
                          ? 'bg-[#f25c24] text-white'
                          : 'text-[#786558] hover:text-[#1e140f]'
                      }`}
                    >
                      Preview
                    </button>
                    <button
                      onClick={() => setActiveTab('citations')}
                      className={`px-3 py-1 rounded-lg ${
                        activeTab === 'citations'
                          ? 'bg-[#f25c24] text-white'
                          : 'text-[#786558] hover:text-[#1e140f]'
                      }`}
                    >
                      Citations ({previewDocument.citationsCount || 0})
                    </button>
                    <button
                      onClick={() => setActiveTab('details')}
                      className={`px-3 py-1 rounded-lg ${
                        activeTab === 'details'
                          ? 'bg-[#f25c24] text-white'
                          : 'text-[#786558] hover:text-[#1e140f]'
                      }`}
                    >
                      Details
                    </button>
                  </div>

                  {/* Viewer Box */}
                  <div className="bg-white border border-[#d8cbb8] rounded-2xl p-6 text-xs text-[#2b1f18] leading-relaxed shadow-inner min-h-[280px]">
                    <h4 className="text-sm font-bold text-[#1e140f] mb-2">1. Java Basics</h4>
                    <h5 className="font-semibold text-xs text-[#523e32] mb-3">1.1 The Java Platform</h5>
                    <p className="mb-3 text-[#523e32]">
                      Java is a high-level, class-based, object-oriented programming language designed for portability and performance.
                    </p>
                    <div className="bg-[#fef3c7] p-3 rounded-xl border border-[#fde68a] text-[#92400e] font-medium my-3">
                      “The Java Virtual Machine (JVM) allows Java programs to run on different platforms without modification.”
                    </div>
                    <p className="text-[#523e32]">
                      Key components include the JVM, JRE (Java Runtime Environment), and JDK (Java Development Kit). Memory management is automated via garbage collection.
                    </p>
                    <div className="text-right text-[10px] text-[#8e7869] pt-4">
                      Page 12 of {previewDocument.pages}
                    </div>
                  </div>
                </div>

                {/* Right col: Citation Location box & actions */}
                <div className="space-y-4">
                  <div className="bg-[#f8f3eb] border border-[#e4d9c7] p-4 rounded-2xl space-y-3">
                    <span className="text-[10px] uppercase font-bold text-[#8e7869] tracking-wider block">
                      Citation Location
                    </span>
                    <div className="space-y-1">
                      <div className="font-bold text-xs text-[#1e140f]">Page 12</div>
                      <div className="text-[11px] text-[#786558]">Section 1.1 The Java Platform</div>
                    </div>
                    <blockquote className="text-[11px] italic text-[#5f4e42] border-l-2 border-[#f25c24] pl-2.5 py-0.5">
                      “The Java Virtual Machine (JVM) allows Java programs to run on different platforms without modification.”
                    </blockquote>

                    <button
                      onClick={handleCopyCitation}
                      className="w-full bg-white hover:bg-[#f0e8dc] border border-[#d8cbb8] text-[#1e140f] font-semibold text-xs py-2 rounded-xl flex items-center justify-center gap-1.5 transition-colors"
                    >
                      {copiedCitation ? (
                        <>
                          <Check className="w-3.5 h-3.5 text-emerald-600" />
                          <span>Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-3.5 h-3.5 text-[#786558]" />
                          <span>Copy citation</span>
                        </>
                      )}
                    </button>
                  </div>

                  <button
                    onClick={() => {
                      deleteDocument(previewDocument.id);
                    }}
                    className="w-full border border-red-300 hover:bg-red-50 text-red-600 font-semibold text-xs py-2.5 rounded-xl flex items-center justify-center gap-2 transition-colors"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                    <span>Delete document</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Upload Modal */}
        {isUploadModalOpen && (
          <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
            <div className="bg-[#fdfbf7] text-[#1e140f] border border-[#d8cbb8] rounded-3xl p-6 sm:p-8 max-w-md w-full shadow-2xl relative animate-fade-in">
              <button
                onClick={() => setIsUploadModalOpen(false)}
                className="absolute top-5 right-5 p-1.5 rounded-full hover:bg-[#ede3d3] text-[#786558]"
              >
                <X className="w-5 h-5" />
              </button>

              <h3 className="text-xl font-bold text-[#1e140f]">Upload documents</h3>
              <p className="text-xs text-[#786558] mt-1 mb-4">
                Supported formats: PDF, Markdown, DOCX, TXT. Embedded with BGE Small into local ChromaDB.
              </p>

              <form onSubmit={handleUploadSubmit} className="space-y-4">
                <div>
                  <label className="text-xs font-semibold text-[#1e140f] block mb-1">
                    Document title / filename
                  </label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. spring_boot_guide.pdf"
                    value={uploadName}
                    onChange={e => setUploadName(e.target.value)}
                    className="w-full text-xs p-3 rounded-xl border border-[#cbb8a3] bg-white text-[#1e140f] focus:outline-none focus:ring-1 focus:ring-[#f25c24]"
                  />
                </div>

                <div>
                  <label className="text-xs font-semibold text-[#1e140f] block mb-1">
                    Document Type
                  </label>
                  <select
                    value={uploadType}
                    onChange={e => setUploadType(e.target.value as any)}
                    className="w-full text-xs p-3 rounded-xl border border-[#cbb8a3] bg-white text-[#1e140f] focus:outline-none focus:ring-1 focus:ring-[#f25c24]"
                  >
                    <option value="PDF">PDF (.pdf)</option>
                    <option value="MD">Markdown (.md)</option>
                    <option value="DOCX">Word (.docx)</option>
                    <option value="TXT">Plain text (.txt)</option>
                  </select>
                </div>

                {/* Drag and Drop Zone placeholder */}
                <div className="border-2 border-dashed border-[#cbb8a3] rounded-2xl p-6 text-center space-y-2 bg-[#f8f3eb]">
                  <Upload className="w-8 h-8 text-[#f25c24] mx-auto" />
                  <p className="text-xs font-medium text-[#1e140f]">Drag and drop files here, or browse</p>
                  <p className="text-[10px] text-[#786558]">Maximum file size: 25 MB</p>
                </div>

                <div className="flex items-center justify-end gap-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setIsUploadModalOpen(false)}
                    className="px-4 py-2 text-xs font-semibold text-[#786558]"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2.5 text-xs font-bold bg-[#f25c24] text-white rounded-xl hover:bg-[#d94c17] shadow-md shadow-[#f25c24]/20"
                  >
                    Index document
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
