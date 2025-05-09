import {
  useReactTable,
  getCoreRowModel,
  getFilteredRowModel,
  getSortedRowModel,
  flexRender,
  ColumnDef,
  SortingState,
  RowSelectionState,
} from "@tanstack/react-table";
import { useState } from "react";
import { Table, Form, InputGroup } from "react-bootstrap";
import { BsChevronDown, BsChevronUp } from "react-icons/bs";

// This component was mostly copied from the TanStack Table documentation
// https://tanstack.com/table/v8/docs/examples/react-table
// and modified to fit the needs of the OpenLabel project.

type FileItem = {
  fileId: string;
  projectId: string;
  createdAt: string;
  createdBy: string;
  filename: string;
  size: number;
  contentType: string;
  type: "image" | "text";
  status: "unannotated" | "annotated" | string;
  width?: number;
  height?: number;
};

interface Props {
  files: FileItem[];
  onSelectionChange: (selected: FileItem[]) => void;
}

const ProjectFileTable = ({ files, onSelectionChange }: Props) => {
  const [rowSelection, setRowSelection] = useState<RowSelectionState>({});
  const [globalFilter, setGlobalFilter] = useState("");
  const [sorting, setSorting] = useState<SortingState>([]);

  const columns: ColumnDef<FileItem>[] = [
    {
      id: "select",
      header: ({ table }) => (
        <Form.Check
          type="checkbox"
          checked={table.getIsAllRowsSelected()}
          onChange={table.getToggleAllRowsSelectedHandler()}
        />
      ),
      cell: ({ row }) => (
        <Form.Check
          type="checkbox"
          checked={row.getIsSelected()}
          onChange={row.getToggleSelectedHandler()}
        />
      ),
    },
    {
      header: "Name",
      accessorKey: "filename",
      enableSorting: true,
    },
    {
      header: "Size",
      accessorKey: "size",
      cell: (info) => `${((info.getValue() as number) / 1024).toFixed(2)} KB`,
      enableSorting: true,
    },
    {
      header: "Type",
      accessorKey: "type",
      enableSorting: true,
    },
    {
      header: "Uploaded At",
      accessorKey: "createdAt",
      enableSorting: true,
    },
  ];

  const table = useReactTable({
    data: files,
    columns,
    state: {
      globalFilter,
      rowSelection,
      sorting,
    },
    onGlobalFilterChange: setGlobalFilter,
    onRowSelectionChange: (updater) => {
      const newSelection =
        typeof updater === "function" ? updater(rowSelection) : updater;
      setRowSelection(newSelection);

      const selectedRows = Object.keys(newSelection).map(
        (rowId) => files[parseInt(rowId)]
      );
      onSelectionChange(selectedRows);
    },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getSortedRowModel: getSortedRowModel(),
    enableRowSelection: true,
  });

  return (
    <>
      <InputGroup className="mb-3">
        <Form.Control
          placeholder="Search files..."
          value={globalFilter ?? ""}
          onChange={(e) => setGlobalFilter(e.target.value)}
        />
      </InputGroup>

      <Table striped bordered hover responsive className="rounded-3">
        <thead>
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => {
                const isSortable = header.column.getCanSort();
                const sortDirection = header.column.getIsSorted();
                return (
                  <th
                    key={header.id}
                    onClick={
                      isSortable
                        ? header.column.getToggleSortingHandler()
                        : undefined
                    }
                    style={{ cursor: isSortable ? "pointer" : "default" }}
                  >
                    {flexRender(
                      header.column.columnDef.header,
                      header.getContext()
                    )}
                    {isSortable && (
                      <span className="ms-1">
                        {sortDirection === "asc" && <BsChevronUp />}
                        {sortDirection === "desc" && <BsChevronDown />}
                      </span>
                    )}
                  </th>
                );
              })}
            </tr>
          ))}
        </thead>
        <tbody>
          {table.getRowModel().rows.map((row) => (
            <tr key={row.id}>
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id}>
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </Table>
    </>
  );
};

export default ProjectFileTable;
