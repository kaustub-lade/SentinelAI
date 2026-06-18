import React, { useEffect, useState } from "react"
import { cloudAPI } from "../services/api"
import {ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid} from "recharts"

export default function CloudSecurity() {
  const [findings, setFindings] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadFindings()
  }, [])

  const loadFindings = async () => {
        try {
        const res = await cloudAPI.getFindings()

        setFindings(
            res.data.findings || []
        )
        } catch (err) {
        console.error(
            "Failed to load cloud findings:",
            err
        )
        } finally {
        setLoading(false)
        }
    }
    const handleResolve = (id) => {

    setFindings(prev =>
        prev.map(f =>
        f.id === id
            ? {
                ...f,
                status: "Resolved"
            }
            : f
        )
    )

    }

  const activeFindings =
    findings.filter(
        f => f.status !== "Resolved"
    )

    const criticalCount =
    activeFindings.filter(
        f => f.severity === "Critical"
    ).length

    const highCount =
    activeFindings.filter(
        f => f.severity === "High"
    ).length

    const mediumCount =
    activeFindings.filter(
        f => f.severity === "Medium"
    ).length

  const cloudAssets =
    findings.length * 4

  const riskScore = Math.max(
    0,
    100 -
      criticalCount * 20 -
      highCount * 10 -
      mediumCount * 5
  )

  const riskTrend = [
    { period: "Week 1", score: 92 },
    { period: "Week 2", score: 85 },
    { period: "Week 3", score: 74 },
    { period: "Week 4", score: riskScore }
    ]

  if (loading) {
    return (
      <div className="p-8 text-white">
        Loading Cloud Security...
      </div>
    )
  }

  return (
    <div className="p-8 space-y-6">

      {/* Header */}

      <div>
        <h1 className="text-4xl font-bold text-white">
          Cloud Security Posture
        </h1>

        <p className="text-slate-400 mt-2">
          Monitor cloud misconfigurations,
          identity risks, compliance posture,
          and security findings.
        </p>
      </div>

      {/* Summary Cards */}

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">

        <div className="card p-6">
          <p className="text-slate-400">
            Risk Score
          </p>

          <h2 className="text-4xl font-bold text-white mt-2">
            {riskScore}
          </h2>
        </div>

        <div className="card p-6">
          <p className="text-slate-400">
            Critical Findings
          </p>

          <h2 className="text-4xl font-bold text-red-400 mt-2">
            {criticalCount}
          </h2>
        </div>

        <div className="card p-6">
          <p className="text-slate-400">
            High Risk Findings
          </p>

          <h2 className="text-4xl font-bold text-orange-400 mt-2">
            {highCount}
          </h2>
        </div>

        <div className="card p-6">
          <p className="text-slate-400">
            Cloud Assets
          </p>

          <h2 className="text-4xl font-bold text-blue-400 mt-2">
            {cloudAssets}
          </h2>
        </div>

      </div>

      {/* Security Posture */}

      <div className="card p-6">

        <div className="flex justify-between items-center mb-4">

          <h2 className="text-xl font-bold text-white">
            Security Posture
          </h2>

          <span className="text-white font-semibold">
            {riskScore}%
          </span>

        </div>

        <div className="w-full bg-slate-700 rounded-full h-5 overflow-hidden">

          <div
            className={`h-5 transition-all duration-500
              ${
                riskScore > 85
                  ? "bg-green-500"
                  : riskScore > 60
                  ? "bg-yellow-500"
                  : "bg-red-500"
              }`}
            style={{
              width: `${riskScore}%`
            }}
          />

        </div>

      </div>

      <div className="card p-6">
        <h2 className="text-xl font-bold text-white mb-4">
            Cloud Risk Trend
        </h2>

        <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
            <LineChart data={riskTrend}>

                <CartesianGrid
                strokeDasharray="3 3"
                stroke="#334155"
                />

                <XAxis
                dataKey="period"
                stroke="#94a3b8"
                />

                <YAxis
                stroke="#94a3b8"
                />

                <Tooltip />

                <Line
                type="monotone"
                dataKey="score"
                stroke="#3b82f6"
                strokeWidth={3}
                />

            </LineChart>
            </ResponsiveContainer>
        </div>
        </div>

      {/* Compliance */}

      <div className="card p-6">

        <h2 className="text-xl font-bold text-white mb-4">
          Compliance Status
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">

          <div className="bg-slate-700 p-4 rounded-lg text-green-400">
            ✅ CIS Benchmark
          </div>

          <div className="bg-slate-700 p-4 rounded-lg text-green-400">
            ✅ NIST Framework
          </div>

          <div className="bg-slate-700 p-4 rounded-lg text-yellow-400">
            ⚠ ISO 27001
          </div>

          <div className="bg-slate-700 p-4 rounded-lg text-red-400">
            ❌ PCI-DSS
          </div>

        </div>

      </div>

      {/* Findings Table */}

      <div className="card p-6">

        <h2 className="text-xl font-bold text-white mb-4">
          Cloud Findings
        </h2>

        <div className="overflow-x-auto">

          <table className="w-full">

            <thead>

                <tr className="border-b border-slate-700 text-slate-400">

                <th className="text-left py-3">
                    Severity
                </th>

                <th className="text-left py-3">
                    Finding
                </th>

                <th className="text-left py-3">
                    Resource
                </th>

                <th className="text-left py-3">
                    Status
                </th>

                <th className="text-left py-3">
                    Actions
                </th>

                </tr>

            </thead>

            <tbody>

                {findings.map((finding) => (

                <tr
                    key={finding.id}
                    className="border-b border-slate-800"
                >

                    <td className="py-4">

                    <span
                        className={`px-3 py-1 rounded text-sm
                        ${
                        finding.severity === "Critical"
                            ? "bg-red-900 text-red-300"
                            : finding.severity === "High"
                            ? "bg-orange-900 text-orange-300"
                            : "bg-yellow-900 text-yellow-300"
                        }`}
                    >
                        {finding.severity}
                    </span>

                    </td>

                    <td className="text-white py-4">
                    {finding.title}
                    </td>

                    <td className="text-slate-400 py-4">
                    {finding.resource}
                    </td>

                    <td className="py-4">

                    <span
                        className={`font-medium
                        ${
                        finding.status === "Resolved"
                            ? "text-green-400"
                            : "text-blue-400"
                        }`}
                    >
                        {finding.status || "Open"}
                    </span>

                    </td>

                    <td className="py-4">

                    {finding.status !== "Resolved" ? (

                        <button
                        onClick={() =>
                            handleResolve(
                            finding.id
                            )
                        }
                        className="
                            px-3 py-1
                            bg-green-600
                            hover:bg-green-500
                            rounded
                            text-white
                            text-sm
                        "
                        >
                        Resolve
                        </button>

                    ) : (

                        <span
                        className="
                            text-green-400
                            font-medium
                        "
                        >
                        ✓ Resolved
                        </span>

                    )}

                    </td>

                </tr>

                ))}

            </tbody>

            </table>

        </div>

      </div>
      <div className="card p-6">
        <h2 className="text-xl font-bold text-white mb-4">
            Recommended Actions
        </h2>

        <div className="space-y-4">

            {criticalCount > 0 && (
            <div className="bg-red-900/20 border border-red-800 rounded-lg p-4">
                <h3 className="text-red-400 font-semibold">
                Critical Priority
                </h3>

                <p className="text-slate-300 mt-2">
                Restrict public storage buckets
                and remove anonymous access.
                </p>
            </div>
            )}

            {highCount > 0 && (
            <div className="bg-orange-900/20 border border-orange-800 rounded-lg p-4">
                <h3 className="text-orange-400 font-semibold">
                High Priority
                </h3>

                <p className="text-slate-300 mt-2">
                Enable MFA for privileged
                administrator accounts.
                </p>
            </div>
            )}

            {mediumCount > 0 && (
            <div className="bg-yellow-900/20 border border-yellow-800 rounded-lg p-4">
                <h3 className="text-yellow-400 font-semibold">
                Medium Priority
                </h3>

                <p className="text-slate-300 mt-2">
                Review wildcard IAM
                permissions and enforce
                least privilege.
                </p>
            </div>
            )}

        </div>

        </div>

    </div>
  )
}